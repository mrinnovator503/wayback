import sqlite3
from flask import Flask, request, jsonify, send_from_directory, Response
from datetime import datetime

app = Flask(__name__, static_folder=".")

# ✅ Initialize SQLite Database
conn = sqlite3.connect('student_logs.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    admissionNo TEXT,
                    scanType TEXT,
                    timestamp TEXT,
                    latitude REAL,
                    longitude REAL
                )''')
conn.commit()

@app.route('/scan', methods=['POST'])
def receive_scan():
    data = request.json
    cursor.execute("INSERT INTO logs (name, admissionNo, scanType, timestamp, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?)",
                   (data['name'], data['admissionNo'], data['scanType'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    data['latitude'], data['longitude']))
    conn.commit()
    return jsonify({"message": "Student log added successfully"}), 200
