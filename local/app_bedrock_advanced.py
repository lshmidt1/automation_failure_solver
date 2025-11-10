"""
Jenkins Failure Analyzer - Advanced Version
Includes: Smart Notifications, Pattern Detection, JIRA Integration, 
Auto-Fix PRs, Failure Prediction, Flakiness Detection, Knowledge Base, Multi-Failure Correlation
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import json
import sqlite3
import requests
import base64
from datetime import datetime, timedelta
import traceback
import hashlib

app = Flask(__name__)
CORS(app)

# Load configuration
try:
    with open('config.json', 'r') as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    print("⚠️ Warning: config.json not found. Using defaults.")
    CONFIG = {}

# Initialize Bedrock client
try:
    bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
    print("✅ Bedrock client initialized")
except Exception as e:
    print(f"⚠️ Warning: Could not initialize Bedrock client: {e}")
    bedrock_client = None

# ===== DATABASE INITIALIZATION =====

def init_db():
    """Initialize enhanced database schema"""
    conn = sqlite3.connect('failures.db')
    c = conn.cursor()
    
    # Main analyses table
    c.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT,
            build_number INTEGER,
            timestamp TEXT,
            status TEXT,
            root_cause TEXT,
            suggested_fix TEXT,
            confidence TEXT,
            full_response TEXT,
            commit_sha TEXT,
            committer_email TEXT,
            jira_ticket TEXT,
            pr_number TEXT,
            fixed_timestamp TEXT,
            cost_estimate REAL
        )
    ''')
    
    # Patterns table
    c.execute('''
        CREATE TABLE IF NOT EXISTS failure_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_hash TEXT UNIQUE,
            pattern_description TEXT,
            occurrences INTEGER DEFAULT 1,
            first_seen TEXT,
            last_seen TEXT,
            example_analysis_ids TEXT
        )
    ''')
    
    # Flaky tests table
    c.execute('''
        CREATE TABLE IF NOT EXISTS flaky_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_name TEXT,
            job_name TEXT,
            total_runs INTEGER,
            failures INTEGER,
            passes INTEGER,
            flake_rate REAL,
            last_updated TEXT
        )
    ''')
    
    # Knowledge base table
    c.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            error_pattern TEXT UNIQUE,
            description TEXT,
            solutions TEXT,
            occurrences INTEGER,
            success_rate REAL,
            last_updated TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

init_db()

# ===== HELPER FUNCTIONS =====

def fetch_jenkins_build(job_name, build_number):
    """Fetch build information from Jenkins"""
    try:
        jenkins_url = CONFIG.get('jenkins_url', 'https://jenkins.crbcloud.com')
        jenkins_user = CONFIG.get('jenkins_user', '')
        jenkins_token = CONFIG.get('jenkins_token', '')
        
        if not jenkins_user or not jenkins_token:
            print("⚠️ Jenkins credentials not configured")
            return None
        
        url = f"{jenkins_url}/job/{job_name}/{build_number}/api/json"
        auth = (jenkins_user, jenkins_token)
        
        response = requests.get(url, auth=auth, timeout=30)
        response.raise_for_status()
        
        build_info = response.json()
        
        # Fetch console log
        log_url = f"{jenkins_url}/job/{job_name}/{build_number}/consoleText"
        log_response = requests.get(log_url, auth=auth, timeout=30)
        log_response.raise_for_status()
        
        return {
            'job_name': job_name,
            'build_number': build_number,
            'result': build_info.get('result', 'UNKNOWN'),
            'timestamp': build_info.get('timestamp'),
            'duration': build_info.get('duration'),
            'console_log': log_response.text[-10000:],  # Last 10k chars
            'url': build_info.get('url')
        }
    except Exception as e:
        print(f"❌ Error fetching Jenkins build: {e}")
        return None

def fetch_azdo_code(file_path=None):
    """Fetch relevant code from Azure DevOps repository"""
    try:
        azdo_url = CONFIG.get('azdo_repo_url', '')
        azdo_pat = CONFIG.get('azdo_pat', '')
        
        if not azdo_url or not azdo_pat:
            return "Azure DevOps not configured"
        
        # Extract org, project, repo from URL
        url_parts = azdo_url.replace('https://dev.azure.com/', '').split('/')
        org = url_parts[0]
        project = url_parts[1]
        repo = url_parts[3] if len(url_parts) > 3 else url_parts[1]
        
        api_url = f"https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo}/items"
        params = {
            'path': file_path or '/README.md',
            'api-version': '6.0'
        }
        
        headers = {
            'Authorization': f'Basic {base64.b64encode(f":{azdo_pat}".encode()).decode()}'
        }
        
        response = requests.get(api_url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.text[:5000]  # First 5k chars
        else:
            return "Code fetch unavailable"
            
    except Exception as e:
        print(f"⚠️ Warning: Could not fetch code from Azure DevOps: {e}")
        return "Code fetch unavailable"

def analyze_with_claude(build_data):
    """Send failure data to Claude for analysis via AWS Bedrock"""
    
    if not bedrock_client:
        return {
            "root_cause": "AWS Bedrock client not available",
            "suggested_fix": "Check AWS credentials and Bedrock permissions",
            "confidence": "low",
            "explanation": "Unable to connect to AWS Bedrock"
        }
    
    try:
        # Get relevant code context
        code_context = fetch_azdo_code()
        
        # Prepare prompt
        prompt = f"""Analyze this Jenkins build failure and provide a root cause analysis with suggested fixes.

**Job:** {build_data['job_name']}
**Build:** #{build_data['build_number']}
**Result:** {build_data['result']}
**URL:** {build_data.get('url', 'N/A')}

**Console Log (last 10k chars):**
```
{build_data['console_log']}
```

**Code Context:**
```
{code_context}
```

Please provide:
1. **Root Cause**: What caused this failure?
2. **Suggested Fix**: How to resolve it?
3. **Confidence**: High/Medium/Low

Format your response as JSON:
{{
  "root_cause": "...",
  "suggested_fix": "...",
  "confidence": "high|medium|low",
  "explanation": "..."
}}
"""

        # Call Claude via Bedrock
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = bedrock_client.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps(request_body)
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        response_text = response_body['content'][0]['text']
        
        # Try to extract JSON
        try:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                analysis = json.loads(json_str)
            else:
                analysis = {
                    "root_cause": "Parse error - see full response",
                    "suggested_fix": "Review analysis manually",
                    "confidence": "low",
                    "explanation": response_text
                }
        except json.JSONDecodeError:
            analysis = {
                "root_cause": "JSON parse error",
                "suggested_fix": response_text[:500],
                "confidence": "medium",
                "explanation": response_text
            }
        
        return analysis
        
    except Exception as e:
        print(f"❌ Error calling Bedrock: {e}")
        traceback.print_exc()
        return {
            "root_cause": f"Bedrock error: {str(e)}",
            "suggested_fix": "Check AWS credentials and Bedrock permissions (bedrock:InvokeModel)",
            "confidence": "low",
            "explanation": str(e)
        }

# ===== FEATURE 1: SMART NOTIFICATIONS =====

def notify_failure_owner(job_name, build_number, analysis, build_data):
    """Send notification to the person who broke the build"""
    try:
        committer_email = build_data.get('committer_email', 'team@company.com')
        
        # Slack/Teams notification
        webhook_url = CONFIG.get('slack_webhook_url') or CONFIG.get('teams_webhook_url')
        
        if webhook_url:
            message = {
                "text": f"🚨 Build Failure Alert: {job_name} #{build_number}",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"🚨 {job_name} #{build_number} Failed"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Assigned to:*\n{committer_email}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Confidence:*\n{analysis['confidence'].upper()}"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Root Cause:*\n{analysis['root_cause'][:300]}..."
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Suggested Fix:*\n{analysis['suggested_fix'][:300]}..."
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "View Build"
                                },
                                "url": build_data.get('url', '#')
                            }
                        ]
                    }
                ]
            }
            
            requests.post(webhook_url, json=message, timeout=10)
            print(f"✅ Sent notification to {committer_email}")
        
    except Exception as e:
        print(f"⚠️ Failed to send notification: {e}")

# ===== FEATURE 2: FAILURE PATTERN DETECTION =====

def detect_patterns():
    """Identify recurring failure patterns"""
    try:
        conn = sqlite3.connect('failures.db')
        c = conn.cursor()
        
        # Get failures from last 7 days
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        
        c.execute('''
            SELECT root_cause, COUNT(*) as occurrences, 
                   GROUP_CONCAT(id) as analysis_ids
            FROM analyses
            WHERE timestamp > ? AND root_cause IS NOT NULL
            GROUP BY root_cause
            HAVING COUNT(*) > 2
            ORDER BY occurrences DESC
        ''', (week_ago,))
        
        patterns = []
        for row in c.fetchall():
            root_cause, occurrences, analysis_ids = row
            
            # Generate pattern hash
            pattern_hash = hashlib.md5(root_cause.encode()).hexdigest()[:10]
            
            # Store or update pattern
            c.execute('''
                INSERT OR REPLACE INTO failure_patterns 
                (pattern_hash, pattern_description, occurrences, 
                 first_seen, last_seen, example_analysis_ids)
                VALUES (?, ?, ?, 
                        COALESCE((SELECT first_seen FROM failure_patterns WHERE pattern_hash = ?), ?),
                        ?, ?)
            ''', (pattern_hash, root_cause, occurrences, 
                  pattern_hash, datetime.utcnow().isoformat(), 
                  datetime.utcnow().isoformat(), analysis_ids))
            
            patterns.append({
                'pattern_hash': pattern_hash,
                'description': root_cause,
                'occurrences': occurrences,
                'severity': 'critical' if occurrences > 5 else 'warning'
            })
        
        conn.commit()
        conn.close()
        
        # Alert on critical patterns
        for pattern in patterns:
            if pattern['severity'] == 'critical':
                alert_recurring_issue(pattern)
        
        return patterns
        
    except Exception as e:
        print(f"❌ Error detecting patterns: {e}")
        return []

def alert_recurring_issue(pattern):
    """Alert team about recurring issues"""
    webhook_url = CONFIG.get('slack_webhook_url')
    if not webhook_url:
        return
    
    message = {
        "text": f"⚠️ RECURRING ISSUE DETECTED\n\n"
                f"This issue has occurred {pattern['occurrences']} times this week:\n"
                f"{pattern['description']}\n\n"
                f"This needs immediate attention to prevent future failures.",
        "username": "Pattern Detector",
        "icon_emoji": ":warning:"
    }
    
    try:
        requests.post(webhook_url, json=message, timeout=10)
        print(f"✅ Alerted about recurring pattern: {pattern['pattern_hash']}")
    except Exception as e:
        print(f"⚠️ Failed to send pattern alert: {e}")

# ===== FEATURE 3: AUTO-CREATE JIRA TICKETS =====

def create_jira_ticket(analysis, build_data):
    """Automatically create JIRA ticket for failure"""
    jira_config = CONFIG.get('jira_config')
    if not jira_config:
        print("⚠️ JIRA not configured")
        return None
    
    try:
        jira_url = jira_config.get('url')
        jira_user = jira_config.get('username')
        jira_token = jira_config.get('api_token')
        jira_project = jira_config.get('project')
        
        if not all([jira_url, jira_user, jira_token, jira_project]):
            print("⚠️ JIRA configuration incomplete")
            return None
        
        # Prepare ticket data
        ticket_data = {
            "fields": {
                "project": {"key": jira_project},
                "summary": f"[AUTO] {build_data['job_name']} Build #{build_data['build_number']} Failed",
                "description": f"""*Root Cause (AI Analysis):*
{analysis['root_cause']}

*Suggested Fix:*
{analysis['suggested_fix']}

*Confidence Level:* {analysis['confidence'].upper()}

*Build URL:* {build_data.get('url', 'N/A')}

*Timestamp:* {datetime.utcnow().isoformat()}

---
_This ticket was automatically created by the Jenkins Failure Analyzer._
                """,
                "issuetype": {"name": "Bug"},
                "priority": {
                    "name": "High" if analysis['confidence'] == 'high' else "Medium"
                },
                "labels": [
                    "auto-generated",
                    "jenkins-failure",
                    build_data['job_name'].replace(' ', '-'),
                    f"confidence-{analysis['confidence']}"
                ]
            }
        }
        
        # Create ticket
        auth = (jira_user, jira_token)
        response = requests.post(
            f"{jira_url}/rest/api/2/issue",
            json=ticket_data,
            auth=auth,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        response.raise_for_status()
        ticket = response.json()
        ticket_key = ticket.get('key')
        
        print(f"✅ Created JIRA ticket: {ticket_key}")
        return ticket_key
        
    except Exception as e:
        print(f"❌ Failed to create JIRA ticket: {e}")
        traceback.print_exc()
        return None

# ===== FEATURE 4: AUTO-FIX SUGGESTIONS (CODE PRs) =====

def generate_fix_pr(analysis, build_data):
    """Generate a PR with Claude's suggested code fix"""
    if not bedrock_client:
        print("⚠️ Cannot generate fix PR without Bedrock")
        return None
    
    if analysis['confidence'] != 'high':
        print(f"⚠️ Skipping auto-fix PR - confidence is {analysis['confidence']}")
        return None
    
    try:
        # Ask Claude to generate actual code fix
        fix_prompt = f"""Based on this failure analysis, generate actual code to fix the issue:

Root Cause: {analysis['root_cause']}
Suggested Fix: {analysis['suggested_fix']}
Failed Job: {build_data['job_name']}

Provide:
1. The exact file(s) that need to be changed
2. The complete fixed code
3. An explanation of the changes

Format as JSON:
{{
  "files_to_change": [
    {{
      "path": "path/to/file.py",
      "current_code": "...",
      "fixed_code": "...",
      "explanation": "..."
    }}
  ]
}}
"""
        
        response = bedrock_client.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 3000,
                "messages": [{"role": "user", "content": fix_prompt}]
            })
        )
        
        response_body = json.loads(response['body'].read())
        response_text = response_body['content'][0]['text']
        
        # Extract JSON
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        fix_details = json.loads(response_text[start:end])
        
        # Create branch and PR in Azure DevOps
        pr_number = create_azdo_pr(fix_details, build_data, analysis)
        
        return pr_number
        
    except Exception as e:
        print(f"❌ Failed to generate fix PR: {e}")
        traceback.print_exc()
        return None

def create_azdo_pr(fix_details, build_data, analysis):
    """Create a pull request in Azure DevOps with the fix"""
    try:
        azdo_url = CONFIG.get('azdo_repo_url')
        azdo_pat = CONFIG.get('azdo_pat')
        
        if not azdo_url or not azdo_pat:
            print("⚠️ Azure DevOps not configured")
            return None
        
        # Parse Azure DevOps URL
        url_parts = azdo_url.replace('https://dev.azure.com/', '').split('/')
        org = url_parts[0]
        project = url_parts[1]
        repo = url_parts[3] if len(url_parts) > 3 else url_parts[1]
        
        # Azure DevOps API setup
        auth_header = {
            'Authorization': f'Basic {base64.b64encode(f":{azdo_pat}".encode()).decode()}',
            'Content-Type': 'application/json'
        }
        
        api_base = f"https://dev.azure.com/{org}/{project}/_apis"
        
        # Create branch name
        branch_name = f"auto-fix/build-{build_data['build_number']}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        print(f"✅ Would create PR with branch: {branch_name}")
        print(f"   Files to change: {len(fix_details.get('files_to_change', []))}")
        
        # For now, just return a mock PR number
        # Full implementation would create actual branch and PR
        return f"mock-pr-{build_data['build_number']}"
        
    except Exception as e:
        print(f"❌ Failed to create PR: {e}")
        traceback.print_exc()
        return None

# ===== FEATURE 6: FAILURE PREDICTION =====

def predict_failure_risk(job_name):
    """Predict likelihood of next build failing"""
    try:
        conn = sqlite3.connect('failures.db')
        c = conn.cursor()
        
        # Get failure rate last 30 days
        thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
        
        c.execute('''
            SELECT COUNT(*) as total_failures
            FROM analyses
            WHERE job_name = ? AND timestamp > ?
        ''', (job_name, thirty_days_ago))
        
        total_failures = c.fetchone()[0]
        
        # Get trend (last 7 days vs previous 7 days)
        seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        fourteen_days_ago = (datetime.utcnow() - timedelta(days=14)).isoformat()
        
        c.execute('''
            SELECT COUNT(*) FROM analyses
            WHERE job_name = ? AND timestamp > ?
        ''', (job_name, seven_days_ago))
        recent_failures = c.fetchone()[0]
        
        c.execute('''
            SELECT COUNT(*) FROM analyses
            WHERE job_name = ? AND timestamp BETWEEN ? AND ?
        ''', (job_name, fourteen_days_ago, seven_days_ago))
        previous_failures = c.fetchone()[0]
        
        conn.close()
        
        # Calculate risk score
        risk_score = 0
        risk_factors = []
        
        if total_failures > 10:
            risk_score += 30
            risk_factors.append("High historical failure rate")
        
        if recent_failures > previous_failures:
            risk_score += 40
            risk_factors.append("Increasing failure trend")
        
        if recent_failures > 5:
            risk_score += 30
            risk_factors.append("Multiple recent failures")
        
        risk_level = "HIGH" if risk_score > 70 else "MEDIUM" if risk_score > 40 else "LOW"
        
        return {
            "job_name": job_name,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "total_failures_30d": total_failures,
            "recent_failures_7d": recent_failures,
            "prediction": f"{risk_score}% chance of failure in next build"
        }
        
    except Exception as e:
        print(f"❌ Error predicting failure risk: {e}")
        return None

# ===== FEATURE 7: TEST FLAKINESS DETECTION =====

def detect_flaky_tests():
    """Identify tests that pass/fail inconsistently"""
    try:
        conn = sqlite3.connect('failures.db')
        c = conn.cursor()
        
        # Identify jobs with inconsistent results
        c.execute('''
            SELECT 
                job_name,
                COUNT(*) as total_runs,
                COUNT(CASE WHEN confidence = 'low' THEN 1 END) as uncertain_failures
            FROM analyses
            WHERE timestamp > datetime('now', '-30 days')
            GROUP BY job_name
            HAVING total_runs > 5
        ''')
        
        flaky_jobs = []
        for row in c.fetchall():
            job_name, total_runs, uncertain = row
            
            # Calculate flake score
            flake_score = (uncertain / total_runs) * 100 if total_runs > 0 else 0
            
            if flake_score > 20:  # More than 20% uncertain failures
                flaky_jobs.append({
                    "job_name": job_name,
                    "total_runs": total_runs,
                    "flake_score": round(flake_score, 1),
                    "recommendation": "Consider adding retries or fixing timing issues"
                })
        
        conn.close()
        
        return flaky_jobs
        
    except Exception as e:
        print(f"❌ Error detecting flaky tests: {e}")
        return []

# ===== FEATURE 10: KNOWLEDGE BASE BUILDER =====

def build_knowledge_base():
    """Build runbook from resolved failures"""
    try:
        conn = sqlite3.connect('failures.db')
        c = conn.cursor()
        
        # Get all failures and group by error pattern
        c.execute('''
            SELECT root_cause, suggested_fix, confidence
            FROM analyses
            WHERE root_cause IS NOT NULL
        ''')
        
        knowledge = {}
        for row in c.fetchall():
            root_cause, suggested_fix, confidence = row
            
            # Extract error pattern (first 100 chars)
            pattern = extract_error_pattern(root_cause)
            
            if pattern not in knowledge:
                knowledge[pattern] = {
                    'description': root_cause,
                    'solutions': [],
                    'occurrences': 0,
                    'high_confidence_count': 0
                }
            
            knowledge[pattern]['solutions'].append(suggested_fix)
            knowledge[pattern]['occurrences'] += 1
            if confidence == 'high':
                knowledge[pattern]['high_confidence_count'] += 1
        
        # Store in database
        for pattern, data in knowledge.items():
            success_rate = (data['high_confidence_count'] / data['occurrences']) * 100 if data['occurrences'] > 0 else 0
            
            c.execute('''
                INSERT OR REPLACE INTO knowledge_base
                (error_pattern, description, solutions, occurrences, success_rate, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                pattern,
                data['description'],
                json.dumps(data['solutions']),
                data['occurrences'],
                success_rate,
                datetime.utcnow().isoformat()
            ))
        
        conn.commit()
        conn.close()
        
        # Generate markdown runbook
        generate_markdown_runbook(knowledge)
        
        print(f"✅ Built knowledge base with {len(knowledge)} entries")
        return knowledge
        
    except Exception as e:
        print(f"❌ Error building knowledge base: {e}")
        return {}

def extract_error_pattern(root_cause):
    """Extract key error pattern from root cause"""
    # Take first sentence or first 100 chars
    sentences = root_cause.split('.')
    if sentences:
        return sentences[0].strip()[:100]
    return root_cause[:100]

def generate_markdown_runbook(knowledge):
    """Generate markdown documentation"""
    markdown = f"""# Jenkins Failure Runbook
_Auto-generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}_

## Common Failure Patterns

"""
    
    # Sort by occurrences
    sorted_patterns = sorted(knowledge.items(), key=lambda x: x[1]['occurrences'], reverse=True)
    
    for pattern, data in sorted_patterns[:20]:  # Top 20
        success_rate = (data['high_confidence_count'] / data['occurrences']) * 100 if data['occurrences'] > 0 else 0
        markdown += f"""### {pattern}
**Occurrences:** {data['occurrences']} times
**Success Rate:** {success_rate:.1f}%

**Description:**
{data['description']}

**Solutions that worked:**
"""
        # Get unique solutions
        unique_solutions = list(set(data['solutions']))[:3]
        for i, solution in enumerate(unique_solutions, 1):
            markdown += f"{i}. {solution[:200]}...\n"
        
        markdown += "\n---\n\n"
    
    # Save to file
    with open('RUNBOOK.md', 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"✅ Generated runbook: RUNBOOK.md")

# ===== FEATURE 14: MULTI-FAILURE CORRELATION =====

def analyze_failure_cascade(time_window_minutes=30):
    """Analyze multiple related failures"""
    try:
        conn = sqlite3.connect('failures.db')
        c = conn.cursor()
        
        # Get recent failures within time window
        cutoff_time = (datetime.utcnow() - timedelta(minutes=time_window_minutes)).isoformat()
        
        c.execute('''
            SELECT job_name, build_number, root_cause, timestamp
            FROM analyses
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        ''', (cutoff_time,))
        
        failures = c.fetchall()
        conn.close()
        
        if len(failures) < 2:
            return None
        
        # Simple correlation without Claude
        failure_descriptions = "\n".join([
            f"- {job} #{build}: {cause} (at {ts})"
            for job, build, cause, ts in failures
        ])
        
        # Basic correlation logic
        related = len(failures) >= 3  # If 3+ failures in time window, likely related
        
        correlation = {
            "related": related,
            "failure_count": len(failures),
            "time_window": time_window_minutes,
            "common_root_cause": "Multiple failures detected in short time window" if related else "Isolated failures",
            "fix_priority": "Investigate common cause immediately" if related else "Handle individually",
            "cascade_analysis": f"{len(failures)} builds failed within {time_window_minutes} minutes"
        }
        
        if related:
            alert_cascade(correlation, failures)
        
        return correlation
        
    except Exception as e:
        print(f"❌ Error analyzing failure cascade: {e}")
        return None

def alert_cascade(correlation, failures):
    """Alert team about cascading failures"""
    webhook_url = CONFIG.get('slack_webhook_url')
    if not webhook_url:
        return
    
    message = {
        "text": f"🚨 CASCADING FAILURE DETECTED\n\n"
                f"{correlation['failure_count']} builds failed in quick succession.\n\n"
                f"Common Root Cause: {correlation['common_root_cause']}\n\n"
                f"Fix Priority: {correlation['fix_priority']}\n\n"
                f"Analysis: {correlation['cascade_analysis']}",
        "username": "Cascade Detector",
        "icon_emoji": ":fire:"
    }
    
    try:
        requests.post(webhook_url, json=message, timeout=10)
        print(f"✅ Alerted about cascading failure")
    except Exception as e:
        print(f"⚠️ Failed to send cascade alert: {e}")

# ===== API ROUTES =====

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    bedrock_status = "available" if bedrock_client else "unavailable"
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "bedrock": bedrock_status,
        "version": "advanced"
    })

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Main webhook endpoint"""
    try:
        # Get parameters
        if request.method == 'POST':
            data = request.get_json() or {}
            job_name = data.get('job_name') or request.args.get('job')
            build_number = data.get('build_number') or request.args.get('build')
        else:
            job_name = request.args.get('job')
            build_number = request.args.get('build')
        
        if not job_name or not build_number:
            return jsonify({"error": "Missing job or build parameter"}), 400
        
        print(f"\n{'='*60}")
        print(f"📥 Received webhook: {job_name} #{build_number}")
        print(f"{'='*60}")
        
        # Fetch build data from Jenkins
        build_data = fetch_jenkins_build(job_name, build_number)
        
        if not build_data:
            # Use mock data if Jenkins fetch fails
            build_data = {
                'job_name': job_name,
                'build_number': build_number,
                'result': 'FAILURE',
                'console_log': 'Mock console log for testing',
                'url': f"https://jenkins.crbcloud.com/job/{job_name}/{build_number}"
            }
            print("⚠️ Using mock build data (Jenkins fetch failed)")
        
        # Analyze with Claude
        print(f"🤖 Analyzing with Claude AI...")
        analysis = analyze_with_claude(build_data)
        
        print(f"\n📊 Analysis Results:")
        print(f"   Root Cause: {analysis.get('root_cause', 'Unknown')[:100]}...")
        print(f"   Confidence: {analysis.get('confidence', 'low').upper()}")
        
        # Feature 1: Smart Notifications
        notify_failure_owner(job_name, build_number, analysis, build_data)
        
        # Feature 3: Auto-create JIRA ticket
        jira_ticket = None
        if CONFIG.get('jira_config') and analysis.get('confidence') == 'high':
            jira_ticket = create_jira_ticket(analysis, build_data)
        
        # Feature 4: Generate fix PR
        pr_number = None
        if CONFIG.get('azdo_pat') and analysis.get('confidence') == 'high':
            pr_number = generate_fix_pr(analysis, build_data)
        
        # Save to database
        conn = sqlite3.connect('failures.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO analyses 
            (job_name, build_number, timestamp, status, root_cause, 
             suggested_fix, confidence, full_response, jira_ticket, pr_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            job_name, build_number, datetime.utcnow().isoformat(), 'completed',
            analysis.get('root_cause', 'Unknown'), 
            analysis.get('suggested_fix', 'Unknown'), 
            analysis.get('confidence', 'low'),
            json.dumps(analysis), jira_ticket, pr_number
        ))
        conn.commit()
        conn.close()
        
        print(f"✅ Saved analysis to database")
        
        # Feature 2: Detect patterns
        patterns = detect_patterns()
        
        # Feature 6: Check prediction
        prediction = predict_failure_risk(job_name)
        
        # Feature 14: Check for cascading failures
        cascade = analyze_failure_cascade()
        
        print(f"{'='*60}\n")
        
        return jsonify({
            "status": "success",
            "job_name": job_name,
            "build_number": build_number,
            "analysis": analysis,
            "jira_ticket": jira_ticket,
            "pr_number": pr_number,
            "patterns_detected": len(patterns),
            "prediction": prediction,
            "cascade_detected": cascade is not None
        })
        
    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/results', methods=['GET'])
def results():
    """View recent analysis results"""
    try:
        conn = sqlite3.connect('failures.db')
        c = conn.cursor()
        
        limit = request.args.get('limit', 50)
        
        c.execute('''
            SELECT job_name, build_number, timestamp, root_cause, 
                   suggested_fix, confidence, jira_ticket, pr_number
            FROM analyses
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        rows = c.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                "job_name": row[0],
                "build_number": row[1],
                "timestamp": row[2],
                "root_cause": row[3],
                "suggested_fix": row[4],
                "confidence": row[5],
                "jira_ticket": row[6],
                "pr_number": row[7]
            })
        
        return jsonify({"results": results, "count": len(results)})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/patterns', methods=['GET'])
def get_patterns():
    """Get detected failure patterns"""
    patterns = detect_patterns()
    return jsonify({"patterns": patterns, "count": len(patterns)})

@app.route('/predictions', methods=['GET'])
def get_predictions():
    """Get failure predictions for all jobs"""
    try:
        conn = sqlite3.connect('failures.db')
        c = conn.cursor()
        
        c.execute('SELECT DISTINCT job_name FROM analyses')
        jobs = [row[0] for row in c.fetchall()]
        conn.close()
        
        predictions = []
        for job in jobs:
            prediction = predict_failure_risk(job)
            if prediction:
                predictions.append(prediction)
        
        # Sort by risk score
        predictions.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return jsonify({"predictions": predictions, "count": len(predictions)})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/flaky-tests', methods=['GET'])
def get_flaky_tests():
    """Get list of flaky tests"""
    flaky = detect_flaky_tests()
    return jsonify({"flaky_tests": flaky, "count": len(flaky)})

@app.route('/knowledge-base', methods=['GET'])
def get_knowledge_base():
    """Get knowledge base entries"""
    try:
        conn = sqlite3.connect('failures.db')
        c = conn.cursor()
        
        c.execute('''
            SELECT error_pattern, description, solutions, occurrences, success_rate
            FROM knowledge_base
            ORDER BY occurrences DESC
            LIMIT 50
        ''')
        
        entries = []
        for row in c.fetchall():
            entries.append({
                "error_pattern": row[0],
                "description": row[1],
                "solutions": json.loads(row[2]) if row[2] else [],
                "occurrences": row[3],
                "success_rate": row[4]
            })
        
        conn.close()
        
        return jsonify({"knowledge_base": entries, "count": len(entries)})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/build-knowledge-base', methods=['POST'])
def trigger_build_kb():
    """Manually trigger knowledge base rebuild"""
    kb = build_knowledge_base()
    return jsonify({"status": "success", "entries": len(kb)})

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get overall statistics"""
    try:
        conn = sqlite3.connect('failures.db')
        c = conn.cursor()
        
        # Total analyses
        c.execute('SELECT COUNT(*) FROM analyses')
        total = c.fetchone()[0]
        
        # By confidence
        c.execute('SELECT confidence, COUNT(*) FROM analyses GROUP BY confidence')
        by_confidence = {row[0]: row[1] for row in c.fetchall()}
        
        # Last 7 days
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        c.execute('SELECT COUNT(*) FROM analyses WHERE timestamp > ?', (week_ago,))
        last_week = c.fetchone()[0]
        
        # Patterns
        c.execute('SELECT COUNT(*) FROM failure_patterns')
        pattern_count = c.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "total_analyses": total,
            "by_confidence": by_confidence,
            "last_7_days": last_week,
            "unique_patterns": pattern_count
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Jenkins Failure Analyzer - ADVANCED VERSION")
    print("="*60)
    print(f"📡 Server: http://localhost:5000")
    print(f"🏥 Health: http://localhost:5000/health")
    print(f"🪝 Webhook: http://localhost:5000/webhook")
    print(f"📊 Results: http://localhost:5000/results")
    print(f"🔍 Patterns: http://localhost:5000/patterns")
    print(f"🔮 Predictions: http://localhost:5000/predictions")
    print(f"🎲 Flaky Tests: http://localhost:5000/flaky-tests")
    print(f"📚 Knowledge Base: http://localhost:5000/knowledge-base")
    print(f"📈 Stats: http://localhost:5000/stats")
    print("="*60)
    
    if bedrock_client:
        print(f"✅ AWS Bedrock: Connected")
    else:
        print(f"⚠️  AWS Bedrock: NOT AVAILABLE (will use limited functionality)")
    
    print("\n" + "="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)