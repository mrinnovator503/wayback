from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime

app = Flask(__name__, static_folder=".")
CORS(app)

# ✅ Initialize SQLite database
DATABASE = "student_logs.db"

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        admissionNo TEXT,
                        scanType TEXT,
                        timestamp TEXT,
                        latitude REAL,
                        longitude REAL,
                        location TEXT)''')
    conn.commit()
    conn.close()

init_db()  # Ensure database is created

# ✅ Function to store log in database
def store_log(name, admission_no, scan_type, latitude, longitude, location):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (name, admissionNo, scanType, timestamp, latitude, longitude, location) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (name, admission_no, scan_type, timestamp, latitude, longitude, location))
    conn.commit()
    conn.close()

# ✅ Handle RFID scan and save log
@app.route('/scan', methods=['POST'])
def receive_scan():
    data = request.json
    name = data.get("name")
    admission_no = data.get("admissionNo")
    scan_type = data.get("scanType")
    latitude = data.get("latitude", 0)
    longitude = data.get("longitude", 0)
    location = f"Lat: {latitude}, Lng: {longitude}"  # Placeholder location

    if not name or not admission_no or not scan_type:
        return jsonify({"error": "Invalid data"}), 400

    store_log(name, admission_no, scan_type, latitude, longitude, location)
    return jsonify({"message": "Student log added successfully"}), 200

# ✅ Get logs for today
@app.route('/logs/today', methods=['GET'])
def get_today_logs():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, admissionNo, scanType, timestamp, location FROM logs WHERE timestamp LIKE ?", (f"{today}%",))
    logs = [{"name": row[0], "admissionNo": row[1], "scanType": row[2], "timestamp": row[3], "location": row[4]} for row in cursor.fetchall()]
    conn.close()
    return jsonify(logs)

# ✅ Serve the dashboard page
@app.route('/')
@app.route('/dashboard.html')
def serve_dashboard():
    return send_from_directory(".", "dashboard.html")

# ✅ Start the Flask server on an available port
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=0, debug=True)
