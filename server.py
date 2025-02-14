from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__, static_folder=".")
CORS(app)

STUDENT_LOGS_FILE = "student_logs.json"

if not os.path.exists(STUDENT_LOGS_FILE):
    with open(STUDENT_LOGS_FILE, "w") as file:
        json.dump([], file)

def load_logs():
    with open(STUDENT_LOGS_FILE, "r") as file:
        return json.load(file)

def save_logs(data):
    with open(STUDENT_LOGS_FILE, "w") as file:
        json.dump(data, file, indent=4)

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

        logs = load_logs()

        logs.append({
            "name": name,
            "admissionNo": admission_no,
            "timestamp": timestamp,
            "latitude": latitude,
            "longitude": longitude
        })

        save_logs(logs)

        return jsonify({"message": "Student log added successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    logs = load_logs()
    return jsonify(logs)

@app.route('/logs/today', methods=['GET'])
def get_today_logs():
    logs = load_logs()
    today = datetime.now().strftime("%Y-%m-%d")
    today_logs = [log for log in logs if log["timestamp"].startswith(today)]
    return jsonify(today_logs)

@app.route('/')
@app.route('/dashboard.html')
def serve_dashboard():
    return send_from_directory(".", "dashboard.html")

@app.route('/download_logs', methods=['GET'])
def download_logs():
    logs = load_logs()
    selected_date = request.args.get("date", "")
    
    if not selected_date:
        return jsonify({"error": "Date not provided"}), 400

    filtered_logs = [log for log in logs if log["timestamp"].startswith(selected_date)]

    if not filtered_logs:
        return jsonify({"error": "No logs found for the selected date"}), 404

    csv_data = "Name,Admission No,Timestamp,Latitude,Longitude\n"
    for log in filtered_logs:
        csv_data += f"{log['name']},{log['admissionNo']},{log['timestamp']},{log['latitude']},{log['longitude']}\n"

    return Response(csv_data, mimetype="text/csv", headers={"Content-Disposition": f"attachment;filename=logs_{selected_date}.csv"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
