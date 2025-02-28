import sqlite3
import cv2
import qrcode
import webbrowser
import base64
import os
from flask import Flask, jsonify, send_file
from flask_cors import CORS
import json  # Import json module for JSON serialization
from threading import Timer, Thread

app = Flask(__name__)
CORS(app, origins="http://localhost:3000")

# SQLite connection
conn = sqlite3.connect('example.db', check_same_thread=False)
cursor = conn.cursor()


# Load class names for object detection
classNames = []
with open("C:/datda manav/Manav/College/SMAPCA/Object_Detection_Files/Data/coco.names", "rt") as f:
    classNames = f.read().rstrip("\n").split("\n")

# Load the pre-trained model for object detection
configPath = "C:/datda manav/Manav/College/SMAPCA/Object_Detection_Files/Data/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
weightsPath = "C:/datda manav/Manav/College/SMAPCA/Object_Detection_Files/Data/frozen_inference_graph.pb"
net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

# Video stream class for handling camera input
class VideoStream:
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
        self.ret, self.frame = self.cap.read()
        self.running = True
        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()

    def update(self):
        while self.running:
            self.ret, self.frame = self.cap.read()

    def read(self):
        return self.ret, self.frame

    def stop(self):
        self.running = False
        self.thread.join()
        self.cap.release()

# Function to detect objects in an image
def getObjects(img, thres, nms):
    if img is None:
        return []
    classIds, confs, bbox = net.detect(img, confThreshold=thres, nmsThreshold=nms)
    objectInfo = []
    if len(classIds) != 0:
        for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
            className = classNames[classId - 1]
            objectInfo.append(className)
    return objectInfo

# Function to generate a QR code
def generate_qr(data):
    # Convert the data to a JSON string
    qr_data = json.dumps(data, indent=4)  # Use indent for pretty-printing (optional)
    
    # Save the QR code
    qr_dir = "static"
    qr_path = os.path.join(qr_dir, "qr_code.png")

    if not os.path.exists(qr_dir):
        os.makedirs(qr_dir)

    # Generate QR code
    qr = qrcode.make(qr_data)
    qr.save(qr_path)
    return qr_path

# Flask route to detect objects and generate QR code
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
        detected_objects1 = getObjects(img1, 0.45, 0.2) if success1 else []
        detected_objects2 = getObjects(img2, 0.45, 0.2) if success2 else []
        detected_objects = set(detected_objects1 + detected_objects2)  # Remove duplicates

        matched_data = []
        qr_data_list = []  # List to store data for QR code

        for obj in detected_objects:
            cursor.execute("SELECT Name, Image, Price, Description FROM Smapca WHERE Name = ?", (obj,))
            db_result = cursor.fetchone()

            if db_result:
                name, image_data, price, description = db_result

                # Add item data to matched_data
                item_data = {
                    "name": name,
                    "price": price,
                    "quantity": 1,  # Default to 1 if not provided
                    "description": description
                }
                matched_data.append(item_data)

                # Add item data to qr_data_list (excluding image)
                qr_data_list.append(item_data)

        # Generate QR code only if items were found
        qr_url = None
        if qr_data_list:
            qr_path = generate_qr(qr_data_list)  # Pass the JSON data to generate_qr
            qr_url = f"http://127.0.0.1:5000/qr_code"

        return jsonify({"success": True, "objects": matched_data, "qr_url": qr_url})

    finally:
        # Stop camera streams
        cap1.stop()
        cap2.stop()

# Flask route to serve the QR code image
@app.route('/qr_code', methods=['GET'])
def get_qr_code():
    return send_file("static/qr_code.png", mimetype='image/png')

# Function to open the browser automatically
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/detect")

# Main entry point
if __name__ == "__main__":
    Timer(1, open_browser).start()  # Open browser after 1 second
    app.run(host='0.0.0.0', port=5000, debug=True)