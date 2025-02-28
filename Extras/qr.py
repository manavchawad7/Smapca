import cv2
import qrcode
import os
from flask import Flask, jsonify, send_file
from flask_cors import CORS
from threading import Thread
from io import BytesIO

app = Flask(__name__)
CORS(app, origins="http://localhost:3000")

# Load class names
classNames = []
with open("coco.names", "rt") as f:
    classNames = f.read().rstrip("\n").split("\n")

# Load model
configPath = "ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
weightsPath = "frozen_inference_graph.pb"
net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

# Object detection function
def getObjects(img, thres, nms, target_classes):
    if img is None:
        return []
    classIds, confs, bbox = net.detect(img, confThreshold=thres, nmsThreshold=nms)
    objectInfo = []
    if len(classIds) != 0:
        for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
            className = classNames[classId - 1]
            if className in target_classes:
                objectInfo.append({
                    "class_name": className,
                    "confidence": round(confidence * 100, 2),
                    "bounding_box": box.tolist()
                })
    return objectInfo

# VideoStream class for threading
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

# Generate and save QR code
import os

def generate_qr(data):
    qr = qrcode.make(data)
    qr_dir = "C:\\datda manav\\Manav\\College\\SMAPCA\\Object_Detection_Files\\Object_Detection_Files\\static"
    qr_path = os.path.join(qr_dir, "qr_code.png")

    if not os.path.exists(qr_dir):
        os.makedirs(qr_dir)

    qr.save(qr_path)
    return qr_path


@app.route('/detect', methods=['GET'])
def detect_objects(): 
    cap1 = VideoStream(0)
    cap2 = VideoStream(1)

    try:
        success1, img1 = cap1.read()
        success2, img2 = cap2.read()

        if not success1 and not success2:
            return jsonify({"success": False, "error": "Unable to read from both cameras"}), 500

        target_classes = ["bottle", "scissors", "backpack", "keyboard", "cell phone"]
        objects1 = getObjects(img1, 0.45, 0.2, target_classes) if success1 else []
        objects2 = getObjects(img2, 0.45, 0.2, target_classes) if success2 else []

        # Merge detected objects
        detected_objects = {obj["class_name"]: obj for obj in objects1 + objects2}
        detected_objects_list = list(detected_objects.values())

        # Generate QR code with object data
        qr_path = generate_qr(str(detected_objects_list))

        return jsonify({"success": True, "objects": detected_objects_list, "qr_url": f"http://127.0.0.1:5000/qr_code"})

    finally:
        cap1.stop()
        cap2.stop()

@app.route('/qr_code', methods=['GET'])
def get_qr_code():
    return send_file("static/qr_code.png", mimetype='image/png')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
