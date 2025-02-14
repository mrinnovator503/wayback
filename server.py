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

@app.route('/logs/<date>', methods=['GET'])
def get_logs_by_date(date):
    logs = load_logs()
    filtered_logs = [log for log in logs if log["timestamp"].startswith(date)]
    return jsonify(filtered_logs)

@app.route('/download_logs/<date>', methods=['GET'])
def download_logs(date):
    logs = load_logs()
    filtered_logs = [log for log in logs if log["timestamp"].startswith(date)]

    csv_data = "Name,Admission No,Timestamp,Latitude,Longitude\n"
    for log in filtered_logs:
        csv_data += f'{log["name"]},{log["admissionNo"]},{log["timestamp"]},{log["latitude"]},{log["longitude"]}\n'

    response = Response(csv_data, mimetype="text/csv")
    response.headers.set("Content-Disposition", f"attachment; filename=logs_{date}.csv")
    return response

@app.route('/')
@app.route('/dashboard.html')
def serve_dashboard():
    return send_from_directory(".", "dashboard.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
