# import cv2
# import numpy as np
# from tensorflow.keras.preprocessing.image import img_to_array
# from tensorflow.keras.models import load_model
# from ultralytics import YOLO
# from PIL import Image
# import json
# import time

# # Load models
# emotion_model = load_model("./models/emotion_model.h5")
# emotion_labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
# yolo_model = YOLO("models/yolov5su.pt")

# # Initialize camera
# camera = cv2.VideoCapture(0)
# face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# def gen_frames():
#     frame_count = 0
#     yolo_results = None

#     while True:
#         success, frame = camera.read()
#         if not success:
#             break

#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         faces = face_cascade.detectMultiScale(gray, 1.3, 5)

#         for (x, y, w, h) in faces:
#             roi = gray[y:y+h, x:x+w]
#             roi = cv2.resize(roi, (48, 48))
#             roi = cv2.cvtColor(roi, cv2.COLOR_GRAY2RGB)
#             roi = roi.astype("float32") / 255.0
#             roi = img_to_array(roi)
#             roi = np.expand_dims(roi, axis=0)
#             preds = emotion_model.predict(roi, verbose=0)[0]
#             label = emotion_labels[np.argmax(preds)]
#             cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
#             cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

#         if frame_count % 5 == 0:
#             yolo_results = yolo_model.predict(frame, verbose=False)

#         if yolo_results:
#             for result in yolo_results:
#                 for box in result.boxes:
#                     x1, y1, x2, y2 = map(int, box.xyxy[0])
#                     conf = float(box.conf[0])
#                     cls = int(box.cls[0])
#                     label = f"{yolo_model.model.names[cls]} {conf:.2f}"
#                     cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
#                     cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

#         frame_count += 1

#         _, buffer = cv2.imencode('.jpg', frame)
#         frame = buffer.tobytes()
#         yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


# def capture_for_30_seconds():
#     detected_emotions = set()
#     detected_objects = set()
#     start_time = time.time()

#     while time.time() - start_time < 30:
#         success, frame = camera.read()
#         if not success:
#             break

#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         faces = face_cascade.detectMultiScale(gray, 1.3, 5)

#         for (x, y, w, h) in faces:
#             roi = gray[y:y+h, x:x+w]
#             roi = cv2.resize(roi, (48, 48))
#             roi = cv2.cvtColor(roi, cv2.COLOR_GRAY2RGB)
#             roi = roi.astype("float32") / 255.0
#             roi = img_to_array(roi)
#             roi = np.expand_dims(roi, axis=0)
#             preds = emotion_model.predict(roi, verbose=0)[0]
#             label = emotion_labels[np.argmax(preds)]
#             detected_emotions.add(label)

#         yolo_results = yolo_model.predict(frame, verbose=False)

#         if yolo_results:
#             for result in yolo_results:
#                 for box in result.boxes:
#                     cls = int(box.cls[0])
#                     label = yolo_model.model.names[cls]
#                     detected_objects.add(label)

#     results = {
#         "emotions": list(detected_emotions),
#         "objects": list(detected_objects)
#     }

#     with open("static/detection_results.json", "w") as f:
#         json.dump(results, f, indent=2)

#     return results


import os
import time
import json
from pathlib import Path

import cv2
import numpy as np
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
from ultralytics import YOLO

# ---------------------------
# Configuration / Paths
# ---------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))        # this file's directory
PROJECT_ROOT = os.path.dirname(BASE_DIR)                     # one level up
STATIC_DIR = os.path.join(PROJECT_ROOT, "static")
Path(STATIC_DIR).mkdir(parents=True, exist_ok=True)

EMOTION_MODEL_PATH = os.path.join(BASE_DIR, "emotion_model.h5")
YOLO_MODEL_PATH = os.path.join(BASE_DIR, "yolov5su.pt")

EMOTION_LABELS = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']

CAMERA_INDEX = 0               # adjust if you need a different camera
YOLO_RUN_EVERY_N_FRAMES = 5    # run YOLO every N frames to save compute
EMOTION_CONF_THRESHOLD = 0.25  # accept predictions above this confidence

# ---------------------------
# Model loading
# ---------------------------
def _load_models():
    if not os.path.exists(EMOTION_MODEL_PATH):
        raise FileNotFoundError(f"Emotion model not found at: {EMOTION_MODEL_PATH}")
    if not os.path.exists(YOLO_MODEL_PATH):
        raise FileNotFoundError(f"YOLO model not found at: {YOLO_MODEL_PATH}")

    emotion_model = load_model(EMOTION_MODEL_PATH)
    yolo_model = YOLO(YOLO_MODEL_PATH)
    return emotion_model, yolo_model

try:
    emotion_model, yolo_model = _load_models()
except Exception as e:
    print(f"[ERROR] Failed to load models: {e}")
    raise

# ---------------------------
# Helpers
# ---------------------------
def _preprocess_face(roi_gray):
    """Preprocess a grayscale face ROI for the emotion model."""
    roi = cv2.resize(roi_gray, (48, 48))
    roi = cv2.cvtColor(roi, cv2.COLOR_GRAY2RGB)  # many emotion models expect 3 channels
    roi = roi.astype("float32") / 255.0
    roi = img_to_array(roi)
    roi = np.expand_dims(roi, axis=0)
    return roi

# ---------------------------
# Streaming generator for Flask
# ---------------------------
def gen_frames(camera_index=CAMERA_INDEX):
    """
    Yield multipart JPEG frames (for Flask stream).
    This function opens its own VideoCapture and releases it on exit to avoid conflicts.
    """
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("[gen_frames] ERROR: Could not open video capture")
        return

    # Warm up camera
    for _ in range(8):
        cap.read()

    frame_count = 0
    yolo_results = None

    try:
        while True:
            success, frame = cap.read()
            if not success:
                print("[gen_frames] Frame read failed")
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40,40))

            for (x, y, w, h) in faces:
                roi_gray = gray[y:y+h, x:x+w]
                try:
                    roi = _preprocess_face(roi_gray)
                    preds = emotion_model.predict(roi, verbose=0)[0]
                    arg = int(np.argmax(preds))
                    max_conf = float(np.max(preds))
                    label = EMOTION_LABELS[arg] if 0 <= arg < len(EMOTION_LABELS) else "Unknown"
                    if max_conf < EMOTION_CONF_THRESHOLD:
                        label = f"{label} (low_conf)"
                except Exception:
                    label = "Unknown"

                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

            # run YOLO every N frames
            if frame_count % YOLO_RUN_EVERY_N_FRAMES == 0:
                try:
                    yolo_results = yolo_model.predict(frame, verbose=False)
                except Exception as e:
                    yolo_results = None
                    print("[gen_frames] YOLO predict error:", e)

            if yolo_results:
                for result in yolo_results:
                    for box in result.boxes:
                        try:
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            conf = float(box.conf[0])
                            cls = int(box.cls[0])
                            label = f"{yolo_model.model.names[cls]} {conf:.2f}"
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                        except Exception:
                            continue

            frame_count += 1
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    finally:
        cap.release()

# ---------------------------
# Capture for N seconds (default 30)
# ---------------------------
def capture_for_30_seconds(save_path=None, duration=30, camera_index=CAMERA_INDEX):
    """
    Capture frames for `duration` seconds, collect detected emotions and objects,
    save results to JSON (default: static/detection_results.json), and return the results dict.
    Also saves up to 5 face samples to static/samples/ for debugging.
    """
    if save_path is None:
        save_path = os.path.join(STATIC_DIR, "detection_results.json")

    samples_dir = os.path.join(os.path.dirname(save_path), "samples")
    Path(samples_dir).mkdir(parents=True, exist_ok=True)
    saved_sample_count = 0

    detected_emotions = set()
    detected_objects = set()

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("[capture_for_30_seconds] ERROR: Could not open video capture")
        return {"emotions": [], "objects": []}

    # warm up camera
    for _ in range(8):
        cap.read()

    start_time = time.time()
    try:
        while time.time() - start_time < duration:
            success, frame = cap.read()
            if not success:
                print("[capture] Frame read failed")
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(40,40))

            # Debug: number of faces in this frame
            print(f"[capture] faces found: {len(faces)}")

            for (x, y, w, h) in faces:
                roi_gray = gray[y:y+h, x:x+w]

                # Save sample images for inspection (first 5)
                if saved_sample_count < 5:
                    try:
                        sample_path = os.path.join(samples_dir, f"face_sample_{saved_sample_count}.png")
                        cv2.imwrite(sample_path, roi_gray)
                        print(f"[capture] saved face sample: {sample_path}")
                        saved_sample_count += 1
                    except Exception as e:
                        print("[capture] failed to save sample:", e)

                try:
                    roi = _preprocess_face(roi_gray)
                    preds = emotion_model.predict(roi, verbose=0)[0]
                    max_conf = float(np.max(preds))
                    arg = int(np.argmax(preds))
                    label = EMOTION_LABELS[arg] if 0 <= arg < len(EMOTION_LABELS) else "Unknown"
                    print(f"[capture] preds: {preds}, max_conf: {max_conf:.4f}, label: {label}")
                    if max_conf >= EMOTION_CONF_THRESHOLD:
                        detected_emotions.add(label)
                    else:
                        print("[capture] low confidence; ignoring emotion")
                except Exception as e:
                    print("[capture] emotion predict error:", e)
                    continue

            # YOLO detection (objects)
            try:
                yolo_results = yolo_model.predict(frame, verbose=False)
                if yolo_results:
                    for result in yolo_results:
                        for box in result.boxes:
                            try:
                                cls = int(box.cls[0])
                                label = yolo_model.model.names[cls]
                                detected_objects.add(label)
                            except Exception:
                                continue
            except Exception as e:
                print("[capture] YOLO error:", e)

    finally:
        cap.release()

    results = {
        "emotions": sorted(list(detected_emotions)),
        "objects": sorted(list(detected_objects))
    }

    try:
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"[capture] Saved detection results to: {save_path}")
    except Exception as e:
        print("[capture] Failed to save detection results:", e)

    print("[capture] Results:", results)
    return results

# ---------------------------
# Quick test when run directly
# ---------------------------
if __name__ == "__main__":
    print("Running capture_for_30_seconds() — make sure your webcam is available.")
    try:
        res = capture_for_30_seconds()
        print(json.dumps(res, indent=2))
    except Exception as e:
        print("Error during capture:", e)
