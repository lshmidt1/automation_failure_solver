"""
Jenkins Failure Analyzer - AWS Bedrock Version
Uses boto3 to call Claude via AWS Bedrock instead of Anthropic API
"""

from flask import Flask, request, jsonify, send_from_directory
import boto3
import json
import sqlite3
import requests
import base64
from datetime import datetime
import traceback
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='../dashboard/dist')
CORS(app)  # Enable CORS for React dev server

# Load configuration
with open('config.json', 'r') as f:
    CONFIG = json.load(f)

# Initialize Bedrock client
try:
    bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
    print("✅ Bedrock client initialized")
except Exception as e:
    print(f"⚠️ Warning: Could not initialize Bedrock client: {e}")
    bedrock_client = None

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('failures.db')
    c = conn.cursor()
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
            full_response TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Fetch Jenkins build info
def fetch_jenkins_build(job_name, build_number):
    """Fetch build information from Jenkins"""
    try:
        url = f"{CONFIG['jenkins_url']}/job/{job_name}/{build_number}/api/json"
        auth = (CONFIG['jenkins_user'], CONFIG['jenkins_token'])
        
        response = requests.get(url, auth=auth, timeout=30)
        response.raise_for_status()
        
        build_info = response.json()
        
        # Fetch console log
        log_url = f"{CONFIG['jenkins_url']}/job/{job_name}/{build_number}/consoleText"
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

# Fetch code from Azure DevOps
def fetch_azdo_code(file_path=None):
    """Fetch relevant code from Azure DevOps repository"""
    try:
        # Extract org, project, repo from URL
        url_parts = CONFIG['azdo_repo_url'].replace('https://dev.azure.com/', '').split('/')
        org = url_parts[0]
        project = url_parts[1]
        repo = url_parts[3] if len(url_parts) > 3 else url_parts[1]
        
        api_url = f"https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo}/items"
        params = {
            'path': file_path or '/README.md',
            'api-version': '6.0'
        }
        
        headers = {
            'Authorization': f'Basic {base64.b64encode(f":{CONFIG["azdo_pat"]}".encode()).decode()}'
        }
        
        response = requests.get(api_url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.text[:5000]  # First 5k chars
        else:
            return "Code fetch unavailable"
            
    except Exception as e:
        print(f"⚠️ Warning: Could not fetch code from Azure DevOps: {e}")
        return "Code fetch unavailable"

# Analyze with Claude AI via Bedrock
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
**URL:** {build_data['url']}

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

# Save analysis to database
def save_analysis(job_name, build_number, analysis):
    """Save analysis results to SQLite database"""
    try:
        conn = sqlite3.connect('failures.db')
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO analyses (job_name, build_number, timestamp, status, 
                                root_cause, suggested_fix, confidence, full_response)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            job_name,
            build_number,
            datetime.utcnow().isoformat(),
            'completed',
            analysis.get('root_cause', 'Unknown'),
            analysis.get('suggested_fix', 'Unknown'),
            analysis.get('confidence', 'low'),
            json.dumps(analysis)
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Saved analysis to database")
        
    except Exception as e:
        print(f"❌ Error saving to database: {e}")

# Post to Slack (optional)
def post_to_slack(job_name, build_number, analysis, build_url):
    """Post analysis results to Slack"""
    if not CONFIG.get('slack_webhook_url'):
        return
    
    try:
        message = {
            "text": f"🔍 Jenkins Failure Analysis: {job_name} #{build_number}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🔍 Failure Analysis: {job_name} #{build_number}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Root Cause:*\n{analysis.get('root_cause', 'Unknown')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Confidence:*\n{analysis.get('confidence', 'low').upper()}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Suggested Fix:*\n{analysis.get('suggested_fix', 'Unknown')}"
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
                            "url": build_url
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(CONFIG['slack_webhook_url'], json=message, timeout=10)
        response.raise_for_status()
        print(f"✅ Posted to Slack")
        
    except Exception as e:
        print(f"⚠️ Warning: Could not post to Slack: {e}")

# Routes
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    bedrock_status = "available" if bedrock_client else "unavailable"
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "bedrock": bedrock_status
    })

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Main webhook endpoint - receives notifications from Jenkins"""
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
        print(f"🔍 Fetching build data from Jenkins...")
        build_data = fetch_jenkins_build(job_name, build_number)
        
        if not build_data:
            return jsonify({"error": "Could not fetch build data"}), 500
        
        print(f"✅ Build data fetched: {build_data['result']}")
        
        # Only analyze failures
        if build_data['result'] not in ['FAILURE', 'UNSTABLE']:
            print(f"ℹ️ Build status is {build_data['result']}, skipping analysis")
            return jsonify({"status": "skipped", "reason": "not a failure"})
        
        # Analyze with Claude
        print(f"🤖 Analyzing with Claude AI (via Bedrock)...")
        analysis = analyze_with_claude(build_data)
        
        print(f"\n📊 Analysis Results:")
        print(f"   Root Cause: {analysis.get('root_cause', 'Unknown')[:100]}...")
        print(f"   Confidence: {analysis.get('confidence', 'low').upper()}")
        
        # Save to database
        save_analysis(job_name, build_number, analysis)
        
        # Post to Slack
        if CONFIG.get('slack_webhook_url'):
            post_to_slack(job_name, build_number, analysis, build_data['url'])
        
        print(f"{'='*60}\n")
        
        return jsonify({
            "status": "success",
            "job_name": job_name,
            "build_number": build_number,
            "analysis": analysis
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
        
        c.execute('''
            SELECT job_name, build_number, timestamp, root_cause, 
                   suggested_fix, confidence
            FROM analyses
            ORDER BY timestamp DESC
            LIMIT 20
        ''')
        
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
                "confidence": row[5]
            })
        
        return jsonify({"results": results, "count": len(results)})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Jenkins Failure Analyzer - AWS Bedrock Version")
    print("="*60)
    print(f"📡 Server starting on http://localhost:5000")
    print(f"🏥 Health check: http://localhost:5000/health")
    print(f"🪝 Webhook endpoint: http://localhost:5000/webhook")
    print(f"📊 Results: http://localhost:5000/results")
    
    if bedrock_client:
        print(f"✅ AWS Bedrock: Connected")
    else:
        print(f"⚠️  AWS Bedrock: NOT AVAILABLE (check credentials)")
    
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

    # Serve React app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')