import cv2
import numpy as np
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
from ultralytics import YOLO
from PIL import Image
import json
import time

# Load models
emotion_model = load_model("./models/emotion_model.h5")
emotion_labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
yolo_model = YOLO("models/yolov5su.pt")

# Initialize camera
camera = cv2.VideoCapture(0)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

def gen_frames():
    frame_count = 0
    yolo_results = None

    while True:
        success, frame = camera.read()
        if not success:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            roi = gray[y:y+h, x:x+w]
            roi = cv2.resize(roi, (48, 48))
            roi = cv2.cvtColor(roi, cv2.COLOR_GRAY2RGB)
            roi = roi.astype("float32") / 255.0
            roi = img_to_array(roi)
            roi = np.expand_dims(roi, axis=0)
            preds = emotion_model.predict(roi, verbose=0)[0]
            label = emotion_labels[np.argmax(preds)]
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

        if frame_count % 5 == 0:
            yolo_results = yolo_model.predict(frame, verbose=False)

        if yolo_results:
            for result in yolo_results:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    label = f"{yolo_model.model.names[cls]} {conf:.2f}"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

        frame_count += 1

        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


def capture_for_30_seconds():
    detected_emotions = set()
    detected_objects = set()
    start_time = time.time()

    while time.time() - start_time < 30:
        success, frame = camera.read()
        if not success:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            roi = gray[y:y+h, x:x+w]
            roi = cv2.resize(roi, (48, 48))
            roi = cv2.cvtColor(roi, cv2.COLOR_GRAY2RGB)
            roi = roi.astype("float32") / 255.0
            roi = img_to_array(roi)
            roi = np.expand_dims(roi, axis=0)
            preds = emotion_model.predict(roi, verbose=0)[0]
            label = emotion_labels[np.argmax(preds)]
            detected_emotions.add(label)

        yolo_results = yolo_model.predict(frame, verbose=False)

        if yolo_results:
            for result in yolo_results:
                for box in result.boxes:
                    cls = int(box.cls[0])
                    label = yolo_model.model.names[cls]
                    detected_objects.add(label)

    results = {
        "emotions": list(detected_emotions),
        "objects": list(detected_objects)
    }

    with open("static/detection_results.json", "w") as f:
        json.dump(results, f, indent=2)

    return results
