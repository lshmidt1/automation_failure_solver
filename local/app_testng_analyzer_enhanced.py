"""
Jenkins Failure Analyzer - TestNG Report Version with Enhanced AI Analysis
Reads TestNG XML reports from uploads or URLs with improved Claude prompting
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import boto3
import json
import sqlite3
import os
from datetime import datetime
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path
import requests
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {'xml'}

# Create folders
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load config
try:
    with open('config.json', 'r') as f:
        CONFIG = json.load(f)
except:
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
    """Initialize database"""
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
            full_response TEXT,
            report_file TEXT,
            test_name TEXT,
            error_message TEXT,
            stack_trace TEXT,
            failure_category TEXT,
            prevention_tips TEXT,
            estimated_fix_time TEXT
        )
    ''')
    
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
    
    conn.commit()
    conn.close()

init_db()

# ===== HELPER FUNCTIONS =====

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_testng_report(file_path):
    """Parse TestNG XML report and extract failure information"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        failures = []
        
        # Find all test cases
        for test_case in root.findall('.//test-method'):
            status = test_case.get('status', 'PASS')
            
            if status == 'FAIL':
                test_name = test_case.get('name', 'Unknown Test')
                class_name = test_case.get('signature', '').split('(')[0] if test_case.get('signature') else 'Unknown'
                
                # Extract exception/error details
                exception = test_case.find('.//exception')
                error_message = ""
                stack_trace = ""
                
                if exception is not None:
                    message_elem = exception.find('message')
                    if message_elem is not None:
                        error_message = message_elem.text or ""
                    
                    full_trace = exception.find('full-stacktrace')
                    if full_trace is not None:
                        stack_trace = full_trace.text or ""
                
                failures.append({
                    'test_name': test_name,
                    'class_name': class_name,
                    'error_message': error_message,
                    'stack_trace': stack_trace,
                    'status': status
                })
        
        return failures
    
    except Exception as e:
        print(f"❌ Error parsing TestNG report {file_path}: {e}")
        return []

def analyze_testng_failure_with_claude(failure_data):
    """Analyze TestNG failure using Claude AI with enhanced prompting"""
    
    if not bedrock_client:
        return {
            "root_cause": f"Test '{failure_data['test_name']}' failed: {failure_data['error_message'][:200]}",
            "suggested_fix": "AWS Bedrock not available. Check error message and stack trace manually.",
            "confidence": "low",
            "failure_category": "unknown",
            "prevention_tips": "Review error manually",
            "estimated_fix_time": "unknown",
            "explanation": "AWS Bedrock not available for AI analysis"
        }
    
    try:
        # Enhanced prompt with more context and structure
        prompt = f"""You are an expert test automation engineer analyzing a TestNG test failure. 
Provide a thorough root cause analysis and actionable fix recommendations.

## Test Failure Details

**Test Name:** {failure_data['test_name']}
**Test Class:** {failure_data['class_name']}

**Error Message:**
```
{failure_data['error_message']}
```

**Stack Trace:**
```
{failure_data['stack_trace'][:3000]}
```

## Analysis Framework

Please analyze this failure systematically:

### 1. Root Cause Analysis
Identify the PRIMARY reason this test failed. Consider:
- Is this a **test code issue** (bad selector, incorrect assertion, flaky waits)?
- Is this an **application bug** (feature broken, API error, data issue)?
- Is this an **environment issue** (timeout, resource unavailable, configuration)?
- Is this a **test data problem** (missing data, wrong state, cleanup issue)?

### 2. Failure Pattern Recognition
- Is this likely a **timing issue** (race condition, element not ready)?
- Is this a **locator problem** (element not found, wrong selector)?
- Is this an **assertion failure** (expected vs actual mismatch)?
- Is this a **network/API issue** (timeout, 404, connection refused)?

### 3. Specific Diagnosis
Based on the error and stack trace:
- What specific line/method failed?
- What was the test trying to do when it failed?
- What condition was not met?

### 4. Actionable Fix
Provide SPECIFIC, ACTIONABLE steps to fix this:
- Exact code changes needed (with examples)
- Configuration changes required
- Test data or environment fixes
- Preventive measures for the future

### 5. Similar Issues Prevention
Suggest how to prevent similar failures:
- Better wait strategies
- Improved error handling
- More robust test design patterns

## Response Format

Provide your analysis in JSON format:
{{
  "root_cause": "Clear, specific explanation of WHY the test failed (2-3 sentences)",
  "failure_category": "test_code_issue|application_bug|environment_issue|test_data_problem|timing_issue",
  "suggested_fix": "Detailed, actionable steps to fix this issue with code examples if applicable",
  "prevention_tips": "How to prevent similar issues in the future",
  "confidence": "high|medium|low",
  "estimated_fix_time": "5 minutes|30 minutes|2 hours|1 day",
  "explanation": "Detailed technical explanation with reasoning"
}}

Be specific, technical, and actionable. Assume the reader is a skilled QA engineer who needs exact guidance.
"""
        
        # Call Claude with higher token limit for detailed response
        response = bedrock_client.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 3000,  # Increased for more detailed analysis
                "temperature": 0.3,   # Lower temperature for more focused responses
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        
        response_body = json.loads(response['body'].read())
        response_text = response_body['content'][0]['text']
        
        # Extract JSON from response
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        if start >= 0 and end > start:
            json_str = response_text[start:end]
            analysis = json.loads(json_str)
            
            # Ensure all fields are present
            if 'failure_category' not in analysis:
                analysis['failure_category'] = 'unknown'
            if 'prevention_tips' not in analysis:
                analysis['prevention_tips'] = 'Review test design patterns'
            if 'estimated_fix_time' not in analysis:
                analysis['estimated_fix_time'] = '30 minutes'
                
        else:
            # Fallback if JSON parsing fails
            analysis = {
                "root_cause": response_text[:800],
                "failure_category": "unknown",
                "suggested_fix": "Review the detailed analysis above",
                "prevention_tips": "Implement better error handling",
                "confidence": "medium",
                "estimated_fix_time": "30 minutes",
                "explanation": response_text
            }
        
        return analysis
    
    except Exception as e:
        print(f"❌ Error analyzing with Claude: {e}")
        traceback.print_exc()
        return {
            "root_cause": failure_data['error_message'][:500],
            "failure_category": "unknown",
            "suggested_fix": "Review stack trace for details",
            "prevention_tips": "Add better error handling",
            "confidence": "low",
            "estimated_fix_time": "unknown",
            "explanation": str(e)
        }

def process_testng_file(file_path, filename):
    """Process a single TestNG file and return results"""
    failures = parse_testng_report(file_path)
    
    if not failures:
        return {
            "status": "no_failures",
            "message": "No failures found in this report",
            "file": filename
        }
    
    results = []
    
    for failure in failures:
        print(f"   🔍 Analyzing: {failure['test_name']}")
        
        analysis = analyze_testng_failure_with_claude(failure)
        
        # Save to database
        conn = sqlite3.connect('failures.db')
        c = conn.cursor()
        
        build_number = int(datetime.utcnow().timestamp())
        
        c.execute('''
            INSERT INTO analyses 
            (job_name, build_number, timestamp, status, root_cause, 
             suggested_fix, confidence, full_response, report_file, 
             test_name, error_message, stack_trace,
             failure_category, prevention_tips, estimated_fix_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            failure['class_name'],
            build_number,
            datetime.utcnow().isoformat(),
            'completed',
            analysis['root_cause'],
            analysis['suggested_fix'],
            analysis['confidence'],
            json.dumps(analysis),
            filename,
            failure['test_name'],
            failure['error_message'],
            failure['stack_trace'],
            analysis.get('failure_category', 'unknown'),
            analysis.get('prevention_tips', ''),
            analysis.get('estimated_fix_time', 'unknown')
        ))
        
        conn.commit()
        conn.close()
        
        results.append({
            "test_name": failure['test_name'],
            "class_name": failure['class_name'],
            "root_cause": analysis['root_cause'],
            "suggested_fix": analysis['suggested_fix'],
            "confidence": analysis['confidence'],
            "failure_category": analysis.get('failure_category'),
            "prevention_tips": analysis.get('prevention_tips'),
            "estimated_fix_time": analysis.get('estimated_fix_time')
        })
    
    return {
        "status": "success",
        "file": filename,
        "failures_analyzed": len(results),
        "results": results
    }

# ===== WEB UI =====

UPLOAD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>TestNG Failure Analyzer - Enhanced</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 900px;
            width: 100%;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 32px;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .upload-section, .url-section {
            margin-bottom: 30px;
            padding: 25px;
            background: #f8f9fa;
            border-radius: 12px;
            border: 2px dashed #ddd;
            transition: all 0.3s;
        }
        
        .upload-section:hover, .url-section:hover {
            border-color: #667eea;
            background: #f0f4ff;
        }
        
        h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 18px;
        }
        
        input[type="file"], input[type="text"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            margin-bottom: 15px;
            transition: border-color 0.3s;
        }
        
        input[type="file"]:focus, input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            display: none;
        }
        
        .status.success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            display: block;
        }
        
        .status.error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            display: block;
        }
        
        .status.loading {
            background: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
            display: block;
        }
        
        .results {
            margin-top: 30px;
        }
        
        .result-item {
            background: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .test-name {
            font-weight: bold;
            color: #667eea;
            margin-bottom: 12px;
            font-size: 18px;
        }
        
        .confidence {
            display: inline-block;
            padding: 6px 14px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 15px;
        }
        
        .confidence.high {
            background: #d4edda;
            color: #155724;
        }
        
        .confidence.medium {
            background: #fff3cd;
            color: #856404;
        }
        
        .confidence.low {
            background: #f8d7da;
            color: #721c24;
        }

        .category-badge {
            display: inline-block;
            background: #e3f2fd;
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 12px;
            margin-left: 10px;
            color: #1976d2;
        }

        .analysis-section {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin: 12px 0;
            border-left: 4px solid #667eea;
        }

        .analysis-section strong {
            display: block;
            margin-bottom: 8px;
            color: #667eea;
            font-size: 14px;
        }

        .analysis-section div {
            color: #333;
            line-height: 1.6;
        }

        .time-estimate {
            color: #666;
            font-size: 13px;
            margin: 10px 0;
        }
        
        .links {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            text-align: center;
        }
        
        .links a {
            color: #667eea;
            text-decoration: none;
            margin: 0 15px;
            font-weight: 500;
        }
        
        .links a:hover {
            text-decoration: underline;
        }

        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 10px auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 TestNG Failure Analyzer</h1>
        <p class="subtitle">Enhanced AI Analysis • Powered by Claude 3.5 Sonnet</p>
        
        <!-- File Upload Section -->
        <div class="upload-section">
            <h3>📁 Upload TestNG XML File</h3>
            <form id="uploadForm" enctype="multipart/form-data">
                <input type="file" id="fileInput" name="file" accept=".xml" required>
                <button type="submit">Analyze File</button>
            </form>
        </div>
        
        <!-- URL Section -->
        <div class="url-section">
            <h3>🔗 Or Provide URL to TestNG Report</h3>
            <form id="urlForm">
                <input type="text" id="urlInput" placeholder="https://example.com/testng-results.xml" required>
                <button type="submit">Analyze from URL</button>
            </form>
        </div>
        
        <!-- Status Messages -->
        <div id="status" class="status"></div>
        
        <!-- Results -->
        <div id="results" class="results"></div>
        
        <!-- Links -->
        <div class="links">
            <a href="/results" target="_blank">View All Results</a>
            <a href="/stats" target="_blank">Statistics</a>
            <a href="http://localhost:3000" target="_blank">Dashboard</a>
        </div>
    </div>
    
    <script>
        // File upload handler
        document.getElementById('uploadForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const fileInput = document.getElementById('fileInput');
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            
            showStatus('loading', '🤖 Analyzing with Claude AI... This may take 30-60 seconds...');
            
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    showStatus('success', `✅ Analyzed ${data.failures_analyzed} test failures from ${data.file}`);
                    displayResults(data.results);
                } else {
                    showStatus('error', data.message || 'Analysis failed');
                }
            } catch (error) {
                showStatus('error', 'Error: ' + error.message);
            }
        });
        
        // URL handler
        document.getElementById('urlForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const url = document.getElementById('urlInput').value;
            
            showStatus('loading', '🤖 Downloading and analyzing... This may take 30-60 seconds...');
            
            try {
                const response = await fetch('/analyze-url', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url: url})
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    showStatus('success', `✅ Analyzed ${data.failures_analyzed} test failures`);
                    displayResults(data.results);
                } else {
                    showStatus('error', data.message || 'Analysis failed');
                }
            } catch (error) {
                showStatus('error', 'Error: ' + error.message);
            }
        });
        
        function showStatus(type, message) {
            const statusDiv = document.getElementById('status');
            statusDiv.className = 'status ' + type;
            
            if (type === 'loading') {
                statusDiv.innerHTML = '<div class="spinner"></div>' + message;
            } else {
                statusDiv.textContent = message;
            }
        }
        
        function displayResults(results) {
            const resultsDiv = document.getElementById('results');
            
            if (!results || results.length === 0) {
                resultsDiv.innerHTML = '';
                return;
            }
            
            let html = '<h3 style="margin: 30px 0 20px 0; color: #333;">📊 Detailed Analysis Results</h3>';
            
            results.forEach(result => {
                html += `
                    <div class="result-item">
                        <div class="test-name">
                            🧪 ${result.test_name}
                            ${result.failure_category ? `<span class="category-badge">${result.failure_category.replace(/_/g, ' ').toUpperCase()}</span>` : ''}
                        </div>
                        <div class="confidence ${result.confidence}">${result.confidence.toUpperCase()} CONFIDENCE</div>
                        ${result.estimated_fix_time ? `<div class="time-estimate">⏱️ Estimated fix time: ${result.estimated_fix_time}</div>` : ''}
                        
                        <div class="analysis-section">
                            <strong>🔍 Root Cause</strong>
                            <div>${result.root_cause}</div>
                        </div>
                        
                        <div class="analysis-section">
                            <strong>💡 Suggested Fix</strong>
                            <div>${result.suggested_fix}</div>
                        </div>
                        
                        ${result.prevention_tips ? `
                            <div class="analysis-section">
                                <strong>🛡️ Prevention Tips</strong>
                                <div>${result.prevention_tips}</div>
                            </div>
                        ` : ''}
                    </div>
                `;
            });
            
            if (results.length > 5) {
                html += `<p style="text-align: center; color: #666; margin-top: 20px;">
                    Showing first results. <a href="/results" target="_blank" style="color: #667eea;">View all ${results.length} analyses</a>
                </p>`;
            }
            
            resultsDiv.innerHTML = html;
        }
    </script>
</body>
</html>
"""

# ===== API ROUTES =====

@app.route('/', methods=['GET'])
def index():
    """Main upload UI"""
    return render_template_string(UPLOAD_HTML)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file provided"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"status": "error", "message": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"status": "error", "message": "Only XML files are allowed"}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        print(f"📁 Processing uploaded file: {filename}")
        result = process_testng_file(filepath, filename)
        
        return jsonify(result)
    
    except Exception as e:
        print(f"❌ Upload error: {e}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/analyze-url', methods=['POST'])
def analyze_url():
    """Analyze TestNG report from URL"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({"status": "error", "message": "No URL provided"}), 400
        
        print(f"🔗 Downloading from URL: {url}")
        
        # Download file
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Save temporarily
        filename = f"url_report_{int(datetime.utcnow().timestamp())}.xml"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"📁 Processing downloaded file: {filename}")
        result = process_testng_file(filepath, filename)
        
        return jsonify(result)
    
    except Exception as e:
        print(f"❌ URL analysis error: {e}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    bedrock_status = "available" if bedrock_client else "unavailable"
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "bedrock": bedrock_status,
        "version": "testng-analyzer-enhanced"
    })

@app.route('/results', methods=['GET'])
def results():
    """View all results"""
    try:
        conn = sqlite3.connect('failures.db')
        c = conn.cursor()
        
        limit = request.args.get('limit', 50)
        
        c.execute('''
            SELECT job_name, build_number, timestamp, root_cause, 
                   suggested_fix, confidence, test_name, error_message, 
                   report_file, failure_category, prevention_tips, estimated_fix_time
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
                "test_name": row[6],
                "error_message": row[7],
                "report_file": row[8],
                "failure_category": row[9],
                "prevention_tips": row[10],
                "estimated_fix_time": row[11]
            })
        
        return jsonify({"results": results, "count": len(results)})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/patterns', methods=['GET'])
def get_patterns():
    """Get detected failure patterns"""
    try:
        conn = sqlite3.connect('failures.db')
        c = conn.cursor()
        
        # Group by similar error messages
        c.execute('''
            SELECT error_message, COUNT(*) as occurrences,
                   GROUP_CONCAT(test_name, ', ') as tests,
                   failure_category
            FROM analyses
            WHERE error_message IS NOT NULL
            GROUP BY error_message
            HAVING COUNT(*) > 1
            ORDER BY occurrences DESC
            LIMIT 10
        ''')
        
        patterns = []
        for row in c.fetchall():
            patterns.append({
                "pattern": row[0][:200],
                "occurrences": row[1],
                "tests": row[2],
                "category": row[3]
            })
        
        conn.close()
        
        return jsonify({"patterns": patterns, "count": len(patterns)})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        
        # By category
        c.execute('SELECT failure_category, COUNT(*) FROM analyses WHERE failure_category IS NOT NULL GROUP BY failure_category')
        by_category = {row[0]: row[1] for row in c.fetchall()}
        
        # Unique tests
        c.execute('SELECT COUNT(DISTINCT test_name) FROM analyses')
        unique_tests = c.fetchone()[0]
        
        # Unique reports
        c.execute('SELECT COUNT(DISTINCT report_file) FROM analyses')
        unique_reports = c.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "total_analyses": total,
            "by_confidence": by_confidence,
            "by_category": by_category,
            "unique_tests": unique_tests,
            "unique_reports": unique_reports
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 TestNG Failure Analyzer - ENHANCED VERSION")
    print("="*60)
    print(f"🌐 Upload Interface: http://localhost:5000")
    print(f"📊 Results API: http://localhost:5000/results")
    print(f"📈 Stats API: http://localhost:5000/stats")
    print(f"🔍 Patterns API: http://localhost:5000/patterns")
    print("="*60)
    
    if bedrock_client:
        print(f"✅ AWS Bedrock: Connected (Enhanced Analysis)")
    else:
        print(f"⚠️  AWS Bedrock: NOT AVAILABLE")
    
    print("\n" + "="*60)
    print("📝 How to Use:")
    print("   1. Open http://localhost:5000 in your browser")
    print("   2. Upload a TestNG XML file OR provide a URL")
    print("   3. Wait for enhanced AI analysis (30-60 seconds)")
    print("   4. View detailed results with:")
    print("      • Root cause analysis")
    print("      • Specific fix recommendations")
    print("      • Prevention tips")
    print("      • Estimated fix time")
    print("      • Failure categorization")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)