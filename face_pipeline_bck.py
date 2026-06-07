import cv2
import numpy as np
import onnxruntime as ort
from config import YU_NET_MODEL_PATH, ARCFACE_MODEL_PATH, DEFAULT_IMAGE_SIZE

# Load YuNet once
detector = cv2.FaceDetectorYN.create(
    YU_NET_MODEL_PATH,
    "",
    (320, 320),
    score_threshold=0.9,
    nms_threshold=0.3,
    top_k=5000,
)

# Load ArcFace once
session = ort.InferenceSession(
    ARCFACE_MODEL_PATH,
    providers=["CPUExecutionProvider"]
)

def detect_best_face(image):
    h, w = image.shape[:2]
    detector.setInputSize((w, h))

    _, faces = detector.detect(image)

    if faces is None or len(faces) == 0:
        return None

    faces = np.array(faces)

    # Pick the highest-confidence face
    best_idx = int(np.argmax(faces[:, 14]))
    face = faces[best_idx]

    bbox = face[:4].astype(int)
    landmarks = face[4:14].reshape(5, 2).astype(np.float32)
    score = float(face[14])

    return {
        "bbox": bbox,
        "landmarks": landmarks,
        "score": score
    }

def align_face(image, landmarks, output_size=DEFAULT_IMAGE_SIZE):
    """
    Align using YuNet 5 landmarks.
    Landmark order:
    left eye, right eye, nose, left mouth, right mouth
    """
    # ArcFace canonical landmarks for 112x112
    dst = np.array([
        [38.2946, 51.6963],
        [73.5318, 51.5014],
        [56.0252, 71.7366],
        [41.5493, 92.3655],
        [70.7299, 92.2041],
    ], dtype=np.float32)

    if output_size == (112, 112):
        dst[:, 0] += 8.0
    else:
        # Scale destination template if you ever change size
        scale_x = output_size[0] / 112.0
        scale_y = output_size[1] / 112.0
        dst[:, 0] = dst[:, 0] * scale_x
        dst[:, 1] = dst[:, 1] * scale_y

    src = landmarks.astype(np.float32)

    M, _ = cv2.estimateAffinePartial2D(src, dst, method=cv2.LMEDS)
    if M is None:
        raise RuntimeError("Could not compute face alignment transform.")

    aligned = cv2.warpAffine(
        image,
        M,
        output_size,
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0)
    )
    return aligned

def get_embedding(aligned_face):
    face = cv2.resize(aligned_face, (112, 112))
    face = face.astype(np.float32)
    face = (face - 127.5) / 128.0
    face = np.transpose(face, (2, 0, 1))
    face = np.expand_dims(face, axis=0)

    input_name = session.get_inputs()[0].name
    output = session.run(None, {input_name: face})[0][0]

    norm = np.linalg.norm(output)
    if norm < 1e-12:
        raise RuntimeError("Embedding norm too small.")

    output = output / norm
    return output
