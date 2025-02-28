import cv2
import webbrowser
from flask import Flask, jsonify
from flask_cors import CORS
from threading import Timer

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

def getObjects(img, thres, nms, target_classes):
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

@app.route('/detect', methods=['GET'])  # Use 'POST' here if needed
def detect_objects():
    cap = cv2.VideoCapture(0)
    
    # Ensure the camera opened correctly
    if not cap.isOpened():
        return jsonify({"success": False, "error": "Unable to open camera"}), 500
    
    success, img = cap.read()
    cap.release()
    
    if success:
        # Define your target classes here
        target_classes = ["bottle", "scissors","backpack","keyboard","cell phone"]  # Add more classes as needed
        objects = getObjects(img, 0.45, 0.2, target_classes)
        return jsonify({"success": True, "objects": objects})
    else:
        return jsonify({"success": False, "error": "Unable to read from camera"}), 500

# Function to open the /detect route in the default web browser
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/detect")

if __name__ == "__main__":
    Timer(1, open_browser).start()  # Open the /detect route after 1 second
    app.run(host='0.0.0.0', port=5000)
