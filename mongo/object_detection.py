import cv2

class ObjectDetector:
    def __init__(self, config_path, weights_path, class_names_path):
        self.classNames = []
        with open(class_names_path, "rt") as f:
            self.classNames = f.read().rstrip("\n").split("\n")

        self.net = cv2.dnn_DetectionModel(weights_path, config_path)
        self.net.setInputSize(320, 320)
        self.net.setInputScale(1.0 / 127.5)
        self.net.setInputMean((127.5, 127.5, 127.5))
        self.net.setInputSwapRB(True)

    def get_objects(self, img, thres=0.45, nms=0.2):
        if img is None:
            return []
        classIds, confs, bbox = self.net.detect(img, confThreshold=thres, nmsThreshold=nms)
        objectInfo = []
        if len(classIds) != 0:
            for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
                className = self.classNames[classId - 1]
                objectInfo.append(className)
        return objectInfo