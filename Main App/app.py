from flask import Flask, jsonify, send_file
from flask_cors import CORS
from threading import Timer
import base64
import os
import sqlite3
from database import Database
from object_detection import ObjectDetector
from qr_generator import QRGenerator
from video_stream import VideoStream

app = Flask(__name__)
CORS(app, origins="http://localhost:3000")

# Initialize modules
# Update Database initialization with SQLite
db = Database("example.db")  # SQLite database name

detector = ObjectDetector(
    "C:/datda manav/Manav/College/SMAPCA/Object_Detection_Files/Data/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt",
    "C:/datda manav/Manav/College/SMAPCA/Object_Detection_Files/Data/frozen_inference_graph.pb",
    "C:/datda manav/Manav/College/SMAPCA/Object_Detection_Files/Data/coco.names"
)
qr_generator = QRGenerator()

@app.route('/detect', methods=['GET'])
def detect_and_fetch():
    cap1 = VideoStream(0)
    cap2 = VideoStream(1)

    try:
        success1, img1 = cap1.read()
        success2, img2 = cap2.read()

        if not success1 and not success2:
            return jsonify({"success": False, "error": "Unable to read from both cameras"}), 500

        detected_objects1 = detector.get_objects(img1) if success1 else []
        detected_objects2 = detector.get_objects(img2) if success2 else []
        detected_objects = set(detected_objects1 + detected_objects2)

        matched_data = []
        qr_data_list = []

        conn = sqlite3.connect("example.db")
        cursor = conn.cursor()

        for obj in detected_objects:
            cursor.execute("SELECT Name, Image, Price, Description FROM Smapca WHERE Name = ?", (obj,))
            db_result = cursor.fetchone()

            if db_result:
                name, image_data, price, description = db_result
                
                if isinstance(image_data, bytes):
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                else:
                    image_base64 = None

                item_data = {
                    "name": name,
                    "price": price,
                    "quantity": 1,
                    "description": description if description else "No description available",
                    "image": image_base64
                }
                matched_data.append(item_data)

                qr_data_list.append({
                    "name": name,
                    "price": price,
                    "quantity": 1,
                    "description": description if description else "No description available"
                })
        
        conn.close()

        qr_url = None
        if qr_data_list:
            qr_path = qr_generator.generate_qr(qr_data_list)
            qr_url = f"http://127.0.0.1:5000/qr_code"

        return jsonify({
            "success": True,
            "objects": matched_data,
            "qr_url": qr_url
        })
    finally:
        cap1.stop()
        cap2.stop()

@app.route('/qr_code', methods=['GET'])
def get_qr_code():
    return send_file("static/qr_code.png", mimetype='image/png')

def open_browser():
    import webbrowser
    webbrowser.open_new("http://127.0.0.1:5000/detect")

if __name__ == "__main__":
    Timer(1, open_browser).start()
    app.run(host='0.0.0.0', port=5000, debug=True)
