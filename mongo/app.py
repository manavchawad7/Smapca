from flask import Flask, jsonify, send_file
from flask_cors import CORS
from threading import Timer
import base64
import os
from database import Database
from object_detection import ObjectDetector
from qr_generator import QRGenerator
from video_stream import VideoStream

app = Flask(__name__)
CORS(app, origins="http://localhost:3000")

# Initialize modules
db = Database('smapca', 'object')
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

        # Detect objects in both camera feeds
        detected_objects1 = detector.get_objects(img1) if success1 else []
        detected_objects2 = detector.get_objects(img2) if success2 else []
        detected_objects = set(detected_objects1 + detected_objects2)  # Remove duplicates

        matched_data = []
        qr_data_list = []  # List to store data for QR code (excluding images)

        for obj in detected_objects:
            db_result = db.find_one({"name": obj})
            if db_result:
                # Handle image data (base64 encoding)
                image_data = db_result.get("image")
                if isinstance(image_data, bytes):
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                else:
                    image_base64 = image_data

                # Extract item details
                name = db_result.get("name", "Unknown")
                price = db_result.get("price", "N/A")
                quantity = db_result.get("quantity", 1)

                # Ensure quantity is a valid number
                if quantity is None or not isinstance(quantity, (int, float)):
                    quantity = 1

                # Add item data to matched_data (for frontend)
                item_data = {
                    "name": name,
                    "price": price,
                    "quantity": quantity,
                    "description": db_result.get("des", "No description available"),
                    "image": image_base64  # Include image for frontend
                }
                matched_data.append(item_data)

                # Add item data to qr_data_list (for QR code, excluding image)
                qr_data_list.append({
                    "name": name,
                    "price": price,
                    "quantity": quantity,
                    "description": db_result.get("des", "No description available")
                })

        # Generate QR code with JSON data (excluding images)
        qr_url = None
        if qr_data_list:
            qr_path = qr_generator.generate_qr(qr_data_list)
            qr_url = f"http://127.0.0.1:5000/qr_code"

        return jsonify({
            "success": True,
            "objects": matched_data,  # Full data for frontend (including images)
            "qr_url": qr_url  # QR code URL
        })

    finally:
        # Stop camera streams
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