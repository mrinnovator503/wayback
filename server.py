from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import json
import os
import time
import requests  # ✅ Added for location lookup
from datetime import datetime

app = Flask(__name__, static_folder=".")
CORS(app)

STUDENT_LOGS_FILE = "student_logs.json"

# ✅ Ensure log file exists
if not os.path.exists(STUDENT_LOGS_FILE):
    with open(STUDENT_LOGS_FILE, "w") as file:
        json.dump([], file)

# ✅ Load logs from file
def load_logs():
    with open(STUDENT_LOGS_FILE, "r") as file:
        return json.load(file)

# ✅ Save logs to file
def save_logs(data):
    with open(STUDENT_LOGS_FILE, "w") as file:
        json.dump(data, file, indent=4)

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

# ✅ Handle RFID scan and save log
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

        logs = load_logs()

        logs.append({
            "name": name,
            "admissionNo": admission_no,
            "timestamp": timestamp,
            "latitude": latitude,
            "longitude": longitude,
            "location": location_name  # ✅ Save human-readable location
        })

        save_logs(logs)

        return jsonify({"message": "Student log added successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Get all logs
@app.route('/logs', methods=['GET'])
def get_logs():
    logs = load_logs()
    return jsonify(logs)

# ✅ Get today's logs
@app.route('/logs/today', methods=['GET'])
def get_today_logs():
    logs = load_logs()
    today = datetime.now().strftime("%Y-%m-%d")
    today_logs = [log for log in logs if log["timestamp"].startswith(today)]
    return jsonify(today_logs)

# ✅ Get last known location
@app.route('/last_location', methods=['GET'])
def get_last_location():
    logs = load_logs()
    valid_logs = [log for log in logs if log["latitude"] != 0 and log["longitude"] != 0]
    
    if not valid_logs:
        return jsonify({"error": "No valid location data available"}), 404

    last_entry = valid_logs[-1]
    return jsonify({
        "latitude": last_entry["latitude"],
        "longitude": last_entry["longitude"],
        "location": last_entry["location"],
        "timestamp": last_entry["timestamp"]
    })

# ✅ Export logs for a selected date as CSV
@app.route('/download_logs', methods=['GET'])
def download_logs():
    logs = load_logs()
    selected_date = request.args.get("date", "")
    
    if not selected_date:
        return jsonify({"error": "Date not provided"}), 400

    filtered_logs = [log for log in logs if log["timestamp"].startswith(selected_date)]

    if not filtered_logs:
        return jsonify({"error": "No logs found for the selected date"}), 404

    csv_data = "Name,Admission No,Timestamp,Location\n"
    for log in filtered_logs:
        csv_data += f"{log['name']},{log['admissionNo']},{log['timestamp']},{log['location']}\n"

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
    app.run(host='0.0.0.0', port=3000, debug=True)
