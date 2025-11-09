"""
Jenkins Failure Analyzer - Mock Version (for testing)
Works without AWS, Jenkins, or Azure DevOps
"""

from flask import Flask, request, jsonify
import json
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Initialize database
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

def mock_analyze(job_name, build_number):
    """Mock AI analysis for testing"""
    return {
        "root_cause": f"Mock analysis for {job_name} build #{build_number}. In production, Claude AI would analyze the actual failure logs.",
        "suggested_fix": "This is a mock response. When AWS Bedrock is connected, you'll get real AI-powered root cause analysis.",
        "confidence": "high",
        "explanation": "This is a test/mock response to verify the system works end-to-end."
    }

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "mode": "mock",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Receive webhook from Jenkins"""
    try:
        if request.method == 'POST':
            data = request.get_json() or {}
            job_name = data.get('job_name') or request.args.get('job')
            build_number = data.get('build_number') or request.args.get('build')
        else:
            job_name = request.args.get('job')
            build_number = request.args.get('build')
        
        if not job_name or not build_number:
            return jsonify({"error": "Missing job or build parameter"}), 400
        
        print(f"\n📥 Webhook received: {job_name} #{build_number}")
        
        # Mock analysis
        analysis = mock_analyze(job_name, build_number)
        
        # Save to database
        conn = sqlite3.connect('failures.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO analyses (job_name, build_number, timestamp, status,
                                root_cause, suggested_fix, confidence, full_response)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            job_name, build_number, datetime.utcnow().isoformat(), 'completed',
            analysis['root_cause'], analysis['suggested_fix'], 
            analysis['confidence'], json.dumps(analysis)
        ))
        conn.commit()
        conn.close()
        
        print(f"✅ Analysis saved to database")
        
        return jsonify({
            "status": "success",
            "mode": "mock",
            "job_name": job_name,
            "build_number": build_number,
            "analysis": analysis
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/results', methods=['GET'])
def results():
    """View recent analyses"""
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

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Jenkins Failure Analyzer - MOCK VERSION")
    print("="*60)
    print("⚠️  This is a test version without AWS/Jenkins integration")
    print("📡 Server: http://localhost:5000")
    print("🏥 Health: http://localhost:5000/health")
    print("🪝 Webhook: http://localhost:5000/webhook?job=test&build=123")
    print("📊 Results: http://localhost:5000/results")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)