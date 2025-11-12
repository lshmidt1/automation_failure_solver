from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "ok", "test": "simple"})

if __name__ == '__main__':
    print("="*60)
    print("TEST: Starting minimal Flask app")
    print("="*60)
    app.run(host='0.0.0.0', port=5000, debug=True)
