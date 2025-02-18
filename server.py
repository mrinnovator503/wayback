from flask import Flask, request, jsonify, send_from_directory, Response
import sqlite3
import os
from datetime import datetime

app = Flask(__name__, static_folder="static")  # ✅ Ensure 'static' folder is correctly referenced
DATABASE_FILE = "student_logs.db"

# ✅ Ensure database exists
def initialize_database():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        admission_no TEXT,
                        scan_type TEXT,
                        timestamp TEXT)''')
    conn.commit()
    conn.close()

initialize_database()

# ✅ Serve the dashboard page
@app.route('/')
@app.route('/dashboard')
def serve_dashboard():
    return send_from_directory("static", "dashboard.html")  # ✅ Ensure dashboard.html is inside 'static' folder

# ✅ Handle RFID scan and save log
@app.route('/scan', methods=['POST'])
def receive_scan():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (name, admission_no, scan_type, timestamp) VALUES (?, ?, ?, ?)",
                   (data["name"], data["admissionNo"], data["scanType"], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

    return jsonify({"message": "Log added"}), 200

# ✅ Start server with dynamic port selection
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port, debug=True)
