import cv2
from threading import Thread

# Load class names
classNames = []
classFile = "coco.names"
with open(classFile, "rt") as f:
    classNames = f.read().rstrip("\n").split("\n")

# Load the model
configPath = "ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
weightsPath = "frozen_inference_graph.pb"
net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

# Threaded Video Capture Class
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

# Object Detection Function
def getObjects(img, thres, nms, draw=True, objects=[]):
    if img is None:
        return img, []
    classIds, confs, bbox = net.detect(img, confThreshold=thres, nmsThreshold=nms)
    if len(objects) == 0:
        objects = classNames
    objectInfo = []
    if len(classIds) != 0:
        for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
            className = classNames[classId - 1]
            if className in objects:
                objectInfo.append({"className": className, "confidence": round(confidence * 100, 2), "box": box})
                if draw:
                    cv2.rectangle(img, box, color=(0, 255, 0), thickness=2)
                    cv2.putText(img, className.upper(), (box[0] + 10, box[1] + 30),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(img, f"{round(confidence * 100, 2)}%", (box[0] + 200, box[1] + 30),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
    return img, objectInfo

# Merge and Filter Unique Detections
def combineDetections(objects1, objects2):
    uniqueObjects = {}
    for obj in objects1 + objects2:
        className = obj["className"]
        # Add object if not already in the unique list
        if className not in uniqueObjects:
            uniqueObjects[className] = obj
    return list(uniqueObjects.values())

# Main Code
if __name__ == "__main__":
    # Initialize video streams for two cameras
    cap1 = VideoStream(0)  # Camera 1
    cap2 = VideoStream(1)  # Camera 2

    while True:
        success1, img1 = cap1.read()
        success2, img2 = cap2.read()

        # Process frames from both cameras
        objectInfo1 = objectInfo2 = []
        if success1 and img1 is not None:
            result1, objectInfo1 = getObjects(img1, 0.45, 0.2)
            cv2.imshow("Camera 1 Output", result1)

        if success2 and img2 is not None:
            result2, objectInfo2 = getObjects(img2, 0.45, 0.2)
            cv2.imshow("Camera 2 Output", result2)

        # Combine unique detections from both cameras
        combinedObjects = combineDetections(objectInfo1, objectInfo2)

        # Print unique objects
        if combinedObjects:
            print("\n--- Combined Detections ---")
            for obj in combinedObjects:
                print(f"Object: {obj['className']}, Confidence: {obj['confidence']}%")

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Stop video streams and release resources
    cap1.stop()
    cap2.stop()
    cv2.destroyAllWindows()
