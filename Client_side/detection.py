from PyQt5.QtCore import QThread, Qt, pyqtSignal
from PyQt5.QtGui import QImage
import cv2
import numpy as np
import time
import requests

class Detection(QThread):
    changePixmap = pyqtSignal(QImage)

    def __init__(self, token, location, receiver):
        super(Detection, self).__init__()
        self.token = token
        self.location = location
        self.receiver = receiver
        self.models = self.load_models()

    def load_models(self):
        # List of dictionaries containing weights, config, and class names for each model
        model_configs = [
            {"weights": "cfg/yolov4.weights", "config": "cfg/yolov4-obj.cfg", "classes": "obj.names"},
            {"weights": "weights/yolov4-obj_4000.weights", "config": "cfg/yolov4-obj.cfg", "classes": "objFire.names"},
        ]

        models = []
        for config in model_configs:
            net = cv2.dnn.readNet(config["weights"], config["config"])
            with open(config["classes"], "r") as f:
                classes = [line.strip() for line in f.readlines()]
            models.append({"net": net, "classes": classes})

        return models

    def run(self):
        self.running = True

        font = cv2.FONT_HERSHEY_PLAIN
        starting_time = time.time()

        # Change the video capture source to the IP camera URL
        ip_camera_url = 'http://192.168.100.117:8080/video'  # Replace with your IP camera URL
        # cap = cv2.VideoCapture(ip_camera_url)
        cap = cv2.VideoCapture(0)

        while self.running:
            ret, frame = cap.read()
            if ret:
                height, width, channels = frame.shape
                all_boxes = []
                all_scores = []
                all_class_ids = []
                all_labels = []

                for model_info in self.models:
                    net = model_info["net"]
                    classes = model_info["classes"]

                    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
                    net.setInput(blob)
                    output_layers = [net.getLayerNames()[i - 1] for i in net.getUnconnectedOutLayers()]
                    outs = net.forward(output_layers)

                    class_ids, confidences, boxes = [], [], []
                    for out in outs:
                        for detection in out:
                            scores = detection[5:]
                            class_id = np.argmax(scores)
                            confidence = scores[class_id]

                            if confidence > 0.98:
                                center_x = int(detection[0] * width)
                                center_y = int(detection[1] * height)
                                w = int(detection[2] * width)
                                h = int(detection[3] * height)

                                x = int(center_x - w / 2)
                                y = int(center_y - h / 2)

                                boxes.append([x, y, w, h])
                                confidences.append(float(confidence))
                                class_ids.append(class_id)

                    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.8, 0.3)

                    for i in range(len(boxes)):
                        if i in indexes:
                            x, y, w, h = boxes[i]
                            all_boxes.append([x, y, w, h])
                            all_scores.append(confidences[i])
                            all_class_ids.append(class_ids[i])
                            all_labels.append(classes[class_ids[i]])

                for i in range(len(all_boxes)):
                    x, y, w, h = all_boxes[i]
                    label = all_labels[i]
                    confidence = all_scores[i]

                    color = (256, 0, 0)

                    # Adjust the scaling factor to reduce the size of the bounding box
                    scale_factor = 0.5  # You can adjust this value as needed

                    # Calculate the adjusted coordinates for the bounding box
                    x1 = max(0, int(x + (1 - scale_factor) * w / 2))
                    y1 = max(0, int(y + (1 - scale_factor) * h / 2))
                    x2 = min(width, int(x + (1 + scale_factor) * w / 2))
                    y2 = min(height, int(y + (1 + scale_factor) * h / 2))

                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, label + " {0:.1%}".format(confidence), (x1, y1 - 20), font, 3, color, 3)

                    elapsed_time = starting_time - time.time()

                    if elapsed_time <= -10:
                        starting_time = time.time()
                        self.save_detection(frame)

                rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                bytesPerLine = channels * width
                convertToQtFormat = QImage(rgbImage.data, width, height, bytesPerLine, QImage.Format_RGB888)
                p = convertToQtFormat.scaled(854, 480, Qt.KeepAspectRatio)
                self.changePixmap.emit(p)

    def save_detection(self, frame):
        cv2.imwrite("saved_frame/frame.jpg", frame)
        print('Frame Saved')
        self.post_detection()

    def post_detection(self):
        try:
            url = 'http://127.0.0.1:8000/api/images/'
            headers = {'Authorization': 'Token ' + self.token}
            files = {'image': open('saved_frame/frame.jpg', 'rb')}
            data = {'user_ID': self.token, 'location': self.location, 'alert_receiver': self.receiver}
            response = requests.post(url, files=files, headers=headers, data=data)

            if response.ok:
                print('Alert was sent to the server')
            else:
                print('Unable to send alert to the server')

        except Exception as e:
            print('Unable to access server:', str(e))
