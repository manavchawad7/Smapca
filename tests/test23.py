import pymongo
import cv2
import webbrowser
from flask import Flask, jsonify
from flask_cors import CORS
from threading import Timer
from threading import Thread
import qrcode
from io import BytesIO
import base64

app = Flask(__name__)
CORS(app, origins="http://localhost:3000")  # Enable CORS

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client['smapca']
collection = db['object']

# Load class names
classNames = []
classFile = "C:/datda manav/Manav/College/SMAPCA/Object_Detection_Files/Data/coco.names"
with open(classFile, "rt") as f:
    classNames = f.read().rstrip("\n").split("\n")

# Load model
configPath = "C:/datda manav/Manav/College/SMAPCA/Object_Detection_Files/Data/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
weightsPath = "C:/datda manav/Manav/College/SMAPCA/Object_Detection_Files/Data/frozen_inference_graph.pb"
net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

# VideoStream class for threading
class VideoStream:
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        self.cap.set(cv2.CAP_PROP_FPS, 15)
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

# Object detection function
def getObjects(img, thres, nms):
    if img is None:
        return []
    classIds, confs, bbox = net.detect(img, confThreshold=thres, nmsThreshold=nms)
    objectInfo = []
    if len(classIds) != 0:
        for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
            className = classNames[classId - 1]
            objectInfo.append(className)  # Only append the class name
    return objectInfo

# Function to generate QR code
def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert QR code image to base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

@app.route('/detect', methods=['GET'])
def detect_and_fetch():
    cap1 = VideoStream(0)  # Camera 1
    cap2 = VideoStream(1)  # Camera 2

    try:
        # Capture frames
        success1, img1 = cap1.read()
        success2, img2 = cap2.read()

        if not success1 and not success2:
            return jsonify({"success": False, "error": "Unable to read from both cameras"}), 500

        # Detect objects from both cameras
        detected_objects1 = getObjects(img1, 0.45, 0.2) if success1 else []
        detected_objects2 = getObjects(img2, 0.45, 0.2) if success2 else []

        # Combine unique detections
        detected_objects = set(detected_objects1 + detected_objects2)

        # Fetch matching data from MongoDB
        matched_data = []
        for obj in detected_objects:
            db_result = collection.find_one({"name": obj})
            if db_result:
                matched_data.append({
                    "name": db_result.get("name"),
                    "price": db_result.get("price"),
                    "description": db_result.get("des"),
                    "image": db_result.get("image")  # Assuming 'image' is stored as a Base64 string or URL
                })

        # Generate QR code for the matched data (excluding images)
        qr_data = [{"name": item["name"], "price": item["price"], "description": item["description"]} for item in matched_data]
        qr_code_base64 = generate_qr_code(str(qr_data))

        # Calculate grand total
        grand_total = sum(item["price"] for item in matched_data)

        # Return matched data, grand total, and QR code URL
        return jsonify({
            "success": True,
            "objects": matched_data,
            "grand_total": grand_total,
            "qr_url": f"data:image/png;base64,{qr_code_base64}"  # Frontend expects this field
        })

    finally:
        # Release camera resources
        cap1.stop()
        cap2.stop()

# Function to open the /detect route in the default web browser
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/detect")

if __name__ == "__main__":
    Timer(1, open_browser).start()  # Open the /detect route after 1 second
    app.run(host='0.0.0.0', port=5000)