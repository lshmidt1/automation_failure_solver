import os, re, json, tempfile, subprocess, boto3, requests
from datetime import datetime

S3_BUCKET   = os.environ["S3_BUCKET"]
DDB_TABLE   = os.environ["DDB_TABLE"]
REPO_URL    = os.environ["REPO_URL"]
REPO_BRANCH = os.environ.get("REPO_BRANCH", "main")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL","")

s3  = boto3.client("s3")
ddb = boto3.resource("dynamodb").Table(DDB_TABLE)
bedrock = boto3.client("bedrock-runtime")

def get_azdo_pat():
    return os.environ.get("AZDO_PAT")

def download_s3_text(key):
    obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
    return obj["Body"].read().decode(errors="ignore")

def analyze_with_claude(console, diff, failed_tests):
    """Use Claude via AWS Bedrock to analyze the failure"""
    
    # Prepare context for Claude
    test_info = ""
    if failed_tests:
        test_info = f"\n\nFailed Tests ({len(failed_tests)}):\n"
        for t in failed_tests[:5]:  # limit to first 5
            test_info += f"- {t.get('className')}.{t.get('name')}\n"
            test_info += f"  Error: {t.get('error')[:200]}\n"
    
    prompt = f"""You are an expert DevOps engineer analyzing a Jenkins build failure.

## Console Log (last 3000 chars):
{console[-3000:]}

## Code Changes (git diff):
{diff[:5000]}
{test_info}

## Your Task:
1. Identify the root cause of this failure
2. Classify the issue type (e.g., "Build/Compilation", "Unit Test Failure", "Network/Timeout", "Credentials", "Memory/Resource", "Infrastructure")
3. Suggest a specific fix or next steps
4. Keep your response concise (under 300 words)

Please respond in this JSON format:
{{
  "category": "Issue Type",
  "root_cause": "Brief description of what went wrong",
  "suggested_fix": "Specific actionable steps to fix this"
}}"""

    try:
        # Call Claude 3 Sonnet via Bedrock
        response = bedrock.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        result = json.loads(response['body'].read())
        content = result['content'][0]['text']
        
        # Try to parse JSON response from Claude
        try:
            analysis = json.loads(content)
            return analysis
        except:
            # If Claude didn't return valid JSON, create structured response
            return {
                "category": "AI Analysis",
                "root_cause": content[:200],
                "suggested_fix": content[200:500] if len(content) > 200 else "Review logs for details"
            }
    
    except Exception as e:
        print(f"Claude analysis failed: {e}")
        # Fallback to simple classification
        return {
            "category": classify_fallback(console, failed_tests),
            "root_cause": "AI analysis unavailable",
            "suggested_fix": "Manual review required"
        }

def classify_fallback(console, failed_tests):
    """Fallback regex-based classification if AI fails"""
    if "OutOfMemoryError" in console or "Java heap space" in console:
        return "Resource/Memory issue"
    if re.search(r"(Failed to connect|timed out|Timeout|ETIMEDOUT)", console, re.I):
        return "Network/Timeout"
    if re.search(r"(AccessDenied|Permission denied|Not authorized|Forbidden)", console, re.I):
        return "Credentials/Permissions"
    if re.search(r"(Compilation failed|cannot find symbol|SyntaxError|TypeError:|npm ERR!)", console, re.I):
        return "Build/Compilation"
    if failed_tests and len(failed_tests) > 0:
        return "Unit/Integration tests"
    if re.search(r"(No space left on device|ENOSPC)", console, re.I):
        return "Agent/Infra (disk space)"
    return "Unknown"

def extract_commit(meta):
    for a in meta.get("actions", []):
        for p in (a.get("parameters") or []):
            if p.get("name") in ("GIT_COMMIT","GIT_REVISION","SHA"):
                return p.get("value")
    if meta.get("changeSet", {}).get("items"):
        return meta["changeSet"]["items"][0].get("commitId")
    return None

def git_diff_for_commit(sha, pat):
    if not sha:
        return ""
    with tempfile.TemporaryDirectory() as d:
        url = REPO_URL
        if pat and url.startswith("https://"):
            url = url.replace("https://", f"https://:{pat}@")
        try:
            subprocess.check_call(["git", "clone", "--no-checkout", "--filter=tree:0", url, d], 
                                stderr=subprocess.DEVNULL, timeout=60)
            subprocess.check_call(["git", "-C", d, "fetch", "origin", sha, "--depth", "1"], 
                                stderr=subprocess.DEVNULL, timeout=60)
            parents = subprocess.check_output(["git", "-C", d, "rev-list", "--parents", "-n", "1", sha]).decode().strip().split()
            parent_sha = parents[1] if len(parents) > 1 else f"{sha}~1"
            diff = subprocess.check_output(["git", "-C", d, "diff", "--unified=0", parent_sha, sha]).decode(errors="ignore")
            return diff
        except Exception as e:
            print(f"Git diff failed: {e}")
            return ""

def post_slack(text):
    if not SLACK_WEBHOOK_URL:
        return
    try:
        requests.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=10)
    except Exception:
        pass

def handler(event, _ctx):
    record = event["Records"][0]
    msg = json.loads(record["body"])
    prefix = msg["s3_prefix"]

    meta = json.loads(download_s3_text(f"{prefix}/meta.json"))
    console = download_s3_text(f"{prefix}/console.txt")
    tests = None
    try:
        tests = json.loads(download_s3_text(f"{prefix}/tests.json"))
    except Exception:
        pass

    sha = extract_commit(meta)
    diff = git_diff_for_commit(sha, get_azdo_pat())

    # Extract failed test info
    failed_tests = []
    if tests:
        for suite in tests.get("suites", []):
            for c in suite.get("cases", []):
                if (c.get("status") or "").upper() == "FAILED":
                    failed_tests.append({
                        "name": c.get("name"),
                        "className": c.get("className"),
                        "error": (c.get("errorDetails") or "")[:500]
                    })

    # AI Analysis with Claude
    analysis = analyze_with_claude(console, diff, failed_tests)

    item = {
        "pk": meta.get("fullDisplayName","unknown"),
        "sk": str(meta.get("id","")),
        "job": meta.get("fullDisplayName"),
        "build": str(meta.get("id","")),
        "result": meta.get("result"),
        "when": datetime.utcfromtimestamp(meta.get("timestamp",0)/1000).isoformat()+"Z",
        "git_commit": sha or "",
        "cause": analysis.get("category", "Unknown"),
        "root_cause": analysis.get("root_cause", ""),
        "suggested_fix": analysis.get("suggested_fix", ""),
        "failed_tests": failed_tests[:25],
        "diff_excerpt": diff[:50000],
        "links": {
            "jenkins_build": meta.get("url"),
            "s3_prefix": prefix,
        }
    }
    ddb.put_item(Item=item)

    summary = f"""*Build failed:* {item['job']} #{item['build']}
*Category:* {analysis.get('category', 'Unknown')}
*Root Cause:* {analysis.get('root_cause', 'See logs')}
*Suggested Fix:* {analysis.get('suggested_fix', 'Manual review')}
*Commit:* {sha or 'n/a'}
*Failed tests:* {len(failed_tests)}
*Jenkins:* {item['links'].get('jenkins_build','')}"""
    post_slack(summary)

    return {"statusCode": 200, "body": "ok"}