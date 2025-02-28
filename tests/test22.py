import cv2
import webbrowser
from flask import Flask, jsonify
from flask_cors import CORS
from threading import Timer
from threading import Thread

app = Flask(__name__)
CORS(app, origins="http://localhost:3000")  # Enable CORS

# Load class names
classNames = []
classFile = "coco.names"
with open(classFile, "rt") as f:
    classNames = f.read().rstrip("\n").split("\n")

# Load model
configPath = "ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
weightsPath = "frozen_inference_graph.pb"
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

# Combine detections from both cameras
def combineDetections(objects1, objects2):
    uniqueObjects = {}
    for obj in objects1 + objects2:
        className = obj["class_name"]
        # Add object if not already in the unique list
        if className not in uniqueObjects:
            uniqueObjects[className] = obj
    return list(uniqueObjects.values())

@app.route('/detect', methods=['GET'])
def detect_objects():
    cap1 = VideoStream(0)  # Camera 1
    cap2 = VideoStream(1)  # Camera 2

    try:
        # Capture frames
        success1, img1 = cap1.read()
        success2, img2 = cap2.read()

        if not success1 and not success2:
            return jsonify({"success": False, "error": "Unable to read from both cameras"}), 500

        # Define target classes
        target_classes = ["bottle", "scissors", "backpack", "keyboard", "cell phone"]

        # Detect objects
        objects1 = getObjects(img1, 0.45, 0.2, target_classes) if success1 else []
        objects2 = getObjects(img2, 0.45, 0.2, target_classes) if success2 else []

        # Combine unique detections
        combinedObjects = combineDetections(objects1, objects2)

        # Return as JSON
        return jsonify({"success": True, "objects": combinedObjects})

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
