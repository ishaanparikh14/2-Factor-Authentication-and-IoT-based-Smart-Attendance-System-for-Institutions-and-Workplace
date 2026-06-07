import cv2
import numpy as np
import onnxruntime as ort

# Load YuNet
detector = cv2.FaceDetectorYN.create(
    "models/yunet.onnx",
    "",
    (320, 320)
)

# Load ArcFace
session = ort.InferenceSession(
    "models/arcface.onnx",
    providers=["CPUExecutionProvider"]
)

cap = cv2.VideoCapture(0)

ret, frame = cap.read()

if not ret:
    print("Camera Error")
    exit()

h, w = frame.shape[:2]

detector.setInputSize((w, h))

_, faces = detector.detect(frame)

if faces is None:
    print("No Face Found")
    exit()

face = faces[0]

x, y, fw, fh = face[:4].astype(int)

crop = frame[y:y+fh, x:x+fw]

crop = cv2.resize(crop, (112,112))

crop = crop.astype(np.float32)

crop = (crop - 127.5) / 128.0

crop = np.transpose(crop, (2,0,1))

crop = np.expand_dims(crop, axis=0)

embedding = session.run(
    None,
    {"data": crop}
)[0][0]

embedding = embedding / np.linalg.norm(embedding)

print("Embedding Length:", len(embedding))

print("First 10 Values:")

print(embedding[:10])
