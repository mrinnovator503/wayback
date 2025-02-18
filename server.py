from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import sqlite3
import os
import time
import requests
import random
from datetime import datetime

app = Flask(__name__, static_folder=".")
CORS(app)

DB_FILE = "student_logs.db"

# ✅ Initialize SQLite Database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            admission_no TEXT,
            timestamp TEXT,
            latitude REAL,
            longitude REAL,
            location TEXT,
            entry_exit TEXT
        )
    """)
    conn.commit()
    conn.close()

# ✅ Get Last Entry Type (Entry/Exit)
def get_last_scan_type(admission_no):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT entry_exit FROM logs WHERE admission_no = ? ORDER BY timestamp DESC LIMIT 1", (admission_no,))
    last_entry = cursor.fetchone()
    conn.close()
    return "Entry" if last_entry is None or last_entry[0] == "Exit" else "Exit"

# ✅ Convert Latitude/Longitude to Address
def get_location_name(latitude, longitude, retries=3):
    if latitude == 0 and longitude == 0:
        return "Location Unknown"

    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}"
    
    for _ in range(retries):
        try:
            response = requests.get(url, headers={"User-Agent": "student-bus-tracking"}, timeout=3)
            if response.status_code == 200:
                data = response.json()
                return data.get("display_name", "Location Not Found")
            time.sleep(1)
        except Exception as e:
            print(f"Error fetching location name (retrying...): {e}")
            time.sleep(1)
    
    return "Location Lookup Failed"

# ✅ Handle RFID Scan & Save to DB
@app.route('/scan', methods=['POST'])
def receive_scan():
    try:
        data = request.json
        name = data.get("name")
        admission_no = data.get("admissionNo")
        latitude = data.get("latitude", 0)
        longitude = data.get("longitude", 0)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not name or not admission_no:
            return jsonify({"error": "Invalid data"}), 400

        location_name = get_location_name(latitude, longitude)
        entry_exit = get_last_scan_type(admission_no)

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO logs (name, admission_no, timestamp, latitude, longitude, location, entry_exit) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (name, admission_no, timestamp, latitude, longitude, location_name, entry_exit))
        conn.commit()
        conn.close()

        return jsonify({"message": "Student log added successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Get Today's Logs
@app.route('/logs/today', methods=['GET'])
def get_today_logs():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, admission_no, timestamp, location, entry_exit FROM logs WHERE timestamp LIKE ?", (today + "%",))
    logs = cursor.fetchall()
    conn.close()
    return jsonify([{"name": log[0], "admissionNo": log[1], "timestamp": log[2], "location": log[3], "entry_exit": log[4]} for log in logs])

# ✅ Get Last Location
@app.route('/last_location', methods=['GET'])
def get_last_location():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT latitude, longitude, location, timestamp FROM logs WHERE latitude != 0 AND longitude != 0 ORDER BY timestamp DESC LIMIT 1")
    last_entry = cursor.fetchone()
    conn.close()

    if last_entry:
        return jsonify({"latitude": last_entry[0], "longitude": last_entry[1], "location": last_entry[2], "timestamp": last_entry[3]})
    else:
        return jsonify({"error": "No valid location data available"}), 404

# ✅ Export Logs as CSV
@app.route('/download_logs', methods=['GET'])
def download_logs():
    selected_date = request.args.get("date", "")
    
    if not selected_date:
        return jsonify({"error": "Date not provided"}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, admission_no, timestamp, location, entry_exit FROM logs WHERE timestamp LIKE ?", (selected_date + "%",))
    logs = cursor.fetchall()
    conn.close()

    if not logs:
        return jsonify({"error": "No logs found for the selected date"}), 404

    csv_data = "Name,Admission No,Timestamp,Location,Entry/Exit\n"
    for log in logs:
        csv_data += f"{log[0]},{log[1]},{log[2]},{log[3]},{log[4]}\n"

    return Response(csv_data, mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename=logs_{selected_date}.csv"})

# ✅ Serve Dashboard
@app.route('/')
@app.route('/dashboard.html')
def serve_dashboard():
    return send_from_directory(".", "dashboard.html")

# ✅ Run Flask on an Available Port
if __name__ == '__main__':
    init_db()
    port = random.randint(3000, 4000)  # Choose a random port if 3000 is occupied
    print(f"🚀 Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
