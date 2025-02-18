import sqlite3
import os
from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime

app = Flask(__name__, static_folder="static")
DATABASE_FILE = "student_logs.db"

# ✅ Ensure database exists with correct schema
def initialize_database():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # ✅ Drop old table if schema is incorrect
    cursor.execute("DROP TABLE IF EXISTS logs")

    # ✅ Create the correct table
    cursor.execute('''CREATE TABLE logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        admission_no TEXT,
                        scan_type TEXT,
                        timestamp TEXT,
                        latitude REAL,
                        longitude REAL,
                        location TEXT)''')
    conn.commit()
    conn.close()

initialize_database()  # ✅ Ensure table is created correctly

# ✅ Handle RFID scan and save log
@app.route('/scan', methods=['POST'])
def receive_scan():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        name = data.get("name")
        admission_no = data.get("admissionNo")
        scan_type = data.get("scanType")
        latitude = data.get("latitude", 0)
        longitude = data.get("longitude", 0)

        if not name or not admission_no or not scan_type:
            return jsonify({"error": "Missing required fields"}), 400

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO logs (name, admission_no, scan_type, timestamp, latitude, longitude, location) 
                          VALUES (?, ?, ?, ?, ?, ?, ?)''',
                       (name, admission_no, scan_type, timestamp, latitude, longitude, "Location Unknown"))
        conn.commit()
        conn.close()

        return jsonify({"message": "Student log added successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Serve the dashboard page
@app.route('/')
@app.route('/dashboard')
def serve_dashboard():
    return send_from_directory("static", "dashboard.html")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port, debug=True)
