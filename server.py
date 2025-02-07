from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

STUDENT_LOGS_FILE = "student_logs.json"

# Initialize JSON file if not exists
if not os.path.exists(STUDENT_LOGS_FILE):
    with open(STUDENT_LOGS_FILE, "w") as file:
        json.dump([], file)

# Function to load student logs
def load_logs():
    with open(STUDENT_LOGS_FILE, "r") as file:
        return json.load(file)

# Function to save student logs
def save_logs(data):
    with open(STUDENT_LOGS_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Route to receive data from ESP32
@app.route('/scan', methods=['POST'])
def receive_scan():
    try:
        data = request.json
        name = data.get("name")
        admission_no = data.get("admissionNo")
        latitude = data.get("latitude", 0)
        longitude = data.get("longitude", 0)

        if not name or not admission_no:
            return jsonify({"error": "Invalid data"}), 400

        logs = load_logs()

        # Append new student scan log
        logs.append({
            "name": name,
            "admissionNo": admission_no,
            "latitude": latitude,
            "longitude": longitude
        })

        save_logs(logs)

        return jsonify({"message": "Student log added successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to get all student logs (for dashboard)
@app.route('/logs', methods=['GET'])
def get_logs():
    logs = load_logs()
    return jsonify(logs)

# Dashboard Route
@app.route('/')
def dashboard():
    return open("dashboard.html").read()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
