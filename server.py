from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import sqlite3
import time
import requests  # For reverse geolocation
from datetime import datetime
import os

app = Flask(__name__, static_folder=".")
CORS(app)

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
                        timestamp TEXT,
                        latitude REAL,
                        longitude REAL,
                        location TEXT)''')
    conn.commit()
    conn.close()

initialize_database()  # Ensure database is set up

# ✅ Function to convert latitude/longitude to location name
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
            time.sleep(1)  # Wait before retrying
        except Exception as e:
            print(f"Error fetching location name (retrying...): {e}")
            time.sleep(1)
    
    return "Location Lookup Failed"

# ✅ Store student log in the SQLite database
def store_log(name, admission_no, scan_type, latitude, longitude):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    location_name = get_location_name(latitude, longitude)

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO logs (name, admission_no, scan_type, timestamp, latitude, longitude, location) 
                      VALUES (?, ?, ?, ?, ?, ?, ?)''',
                   (name, admission_no, scan_type, timestamp, latitude, longitude, location_name))
    conn.commit()
    conn.close()

# ✅ Handle RFID scan and save log
@app.route('/scan', methods=['POST'])
def receive_scan():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400

        name = data.get("name")
        admission_no = data.get("admissionNo")
        scan_type = data.get("scanType")  # "Entry" or "Exit"
        latitude = data.get("latitude", 0)
        longitude = data.get("longitude", 0)

        if not name or not admission_no or not scan_type:
            return jsonify({"error": "Invalid data"}), 400

        store_log(name, admission_no, scan_type, latitude, longitude)
        return jsonify({"message": "Student log added successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Get today's logs
@app.route('/logs/today', methods=['GET'])
def get_today_logs():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, admission_no, scan_type, timestamp, location FROM logs WHERE timestamp LIKE ?", (today + "%",))
    logs = cursor.fetchall()
    conn.close()

    return jsonify([{"name": log[0], "admissionNo": log[1], "scanType": log[2], "timestamp": log[3], "location": log[4]} for log in logs])

# ✅ Get last known location
@app.route('/last_location', methods=['GET'])
def get_last_location():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT latitude, longitude, location, timestamp FROM logs WHERE latitude != 0 AND longitude != 0 ORDER BY timestamp DESC LIMIT 1")
    last_entry = cursor.fetchone()
    conn.close()

    if not last_entry:
        return jsonify({"error": "No valid location data available"}), 404

    return jsonify({
        "latitude": last_entry[0],
        "longitude": last_entry[1],
        "location": last_entry[2],
        "timestamp": last_entry[3]
    })

# ✅ Export logs for a selected date as CSV
@app.route('/download_logs', methods=['GET'])
def download_logs():
    selected_date = request.args.get("date", "")
    
    if not selected_date:
        return jsonify({"error": "Date not provided"}), 400

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, admission_no, scan_type, timestamp, location FROM logs WHERE timestamp LIKE ?", (selected_date + "%",))
    filtered_logs = cursor.fetchall()
    conn.close()

    if not filtered_logs:
        return jsonify({"error": "No logs found for the selected date"}), 404

    csv_data = "Name,Admission No,Scan Type,Timestamp,Location\n"
    for log in filtered_logs:
        csv_data += f"{log[0]},{log[1]},{log[2]},{log[3]},{log[4]}\n"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=logs_{selected_date}.csv"}
    )

# ✅ Serve the dashboard page
@app.route('/')
@app.route('/dashboard.html')
def serve_dashboard():
    return send_from_directory(".", "dashboard.html")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3000))  # Auto-assign port if available
    app.run(host='0.0.0.0', port=port, debug=True)
