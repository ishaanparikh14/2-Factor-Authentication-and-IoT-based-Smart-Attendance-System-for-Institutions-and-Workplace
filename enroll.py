import argparse
import os
from datetime import datetime

import cv2

from config import ENROLL_IMAGE_DIR
from face_pipeline import detect_best_face, align_face, get_embedding
from qdrant_manager import ensure_collection, upsert_student
from firebase_manager import db
def parse_args():
    parser = argparse.ArgumentParser(description="Enroll a student into Qdrant Cloud")
    parser.add_argument("--image", required=True, help="Path to student face image")
    parser.add_argument("--student_id", required=True, help="Student ID / USN")
    parser.add_argument("--name", required=True, help="Student full name")
    parser.add_argument("--phone", required=True, help="Registered phone number")
    parser.add_argument("--email", default="", help="Optional email")
    parser.add_argument("--department", default="", help="Optional department")
    parser.add_argument("--section", default="", help="Optional section")
    return parser.parse_args()

def main():
    args = parse_args()

    if not os.path.exists(args.image):
        raise FileNotFoundError(f"Image not found: {args.image}")

    os.makedirs(ENROLL_IMAGE_DIR, exist_ok=True)

    image = cv2.imread(args.image)
    if image is None:
        raise RuntimeError("Could not read image. Check file format/path.")

    face_info = detect_best_face(image)
    if face_info is None:
        raise RuntimeError("No face detected in the provided image.")

    bbox = face_info["bbox"]
    landmarks = face_info["landmarks"]
    detection_score = face_info["score"]

    aligned = align_face(image, landmarks)
    embedding = get_embedding(aligned)

    ensure_collection()

    payload = {
        "student_id": args.student_id,
        "name": args.name,
        "phone": args.phone,
        "email": args.email,
        "department": args.department,
        "section": args.section,
        "detection_score": detection_score,
        "enrolled_at": datetime.now().isoformat(timespec="seconds"),
        "source_image": os.path.basename(args.image),
    }

    upsert_student(args.student_id, embedding, payload)
    # Firebase student record

    db.collection(
    "students"
    ).document(
      args.student_id
    ).set(
        {
           "student_id": args.student_id,
           "name": args.name,
           "email": args.email,
           "phone": args.phone,
           "department": args.department,
           "section": args.section,
           "attendance_count": 0,
           "enrolled_at": datetime.now().isoformat(timespec="seconds")
        }
    )
    # Save aligned face locally for debugging / audit
    saved_path = os.path.join(ENROLL_IMAGE_DIR, f"{args.student_id}_aligned.jpg")
    cv2.imwrite(saved_path, aligned)

    print("Enrollment successful")
    print(f"Student ID: {args.student_id}")
    print(f"Name: {args.name}")
    print(f"Saved aligned face: {saved_path}")
    print(f"YuNet score: {detection_score:.4f}")
    print("Embedding size: 512")

if __name__ == "__main__":
    main()
