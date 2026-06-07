import argparse
import cv2

from attendance_db import (
init_db,
record_attendance,
was_marked_recently,
verify_otp,
get_total_classes,
get_student_attendance
)

from face_pipeline import (
detect_best_face,
align_face,
get_embedding
)

from otp_service import (
issue_otp,
hash_otp,
send_attendance_report
)

from qdrant_manager import (
search_embedding
)

from config import FACE_MATCH_THRESHOLD

def parse_args():

```
parser = argparse.ArgumentParser()

parser.add_argument(
    "--image",
    required=False,
    help="Image file path"
)

parser.add_argument(
    "--camera",
    action="store_true",
    help="Capture from webcam"
)

return parser.parse_args()
```

def get_frame(args):

```
if args.image:

    frame = cv2.imread(args.image)

    if frame is None:

        raise RuntimeError(
            f"Cannot read image: {args.image}"
        )

    return frame

if args.camera:

    cap = cv2.VideoCapture(
        0,
        cv2.CAP_V4L2
    )

    if not cap.isOpened():

        raise RuntimeError(
            "Could not open camera"
        )

    ret, frame = cap.read()

    cap.release()

    if not ret:

        raise RuntimeError(
            "Could not capture frame"
        )

    return frame

raise RuntimeError(
    "Provide --image or --camera"
)
```

def main():

```
init_db()

args = parse_args()

frame = get_frame(args)

print("\nDetecting face...")

face_info = detect_best_face(
    frame
)

if face_info is None:

    print("No face detected")

    return

aligned = align_face(
    frame,
    face_info["landmarks"]
)

embedding = get_embedding(
    aligned
)

print(
    "Searching Qdrant..."
)

results = search_embedding(
    embedding,
    limit=1
)

if not results:

    print(
        "No match found"
    )

    return

best = results[0]

similarity = float(
    best.score
)

payload = best.payload

if payload is None:

    print(
        "Invalid payload"
    )

    return

student_id = payload.get(
    "student_id",
    ""
)

student_name = payload.get(
    "name",
    ""
)

student_email = payload.get(
    "email",
    ""
)

print("\nMatch Result")

print(
    f"Student ID : {student_id}"
)

print(
    f"Name       : {student_name}"
)

print(
    f"Similarity : {similarity:.4f}"
)

if similarity < FACE_MATCH_THRESHOLD:

    print(
        "\nSimilarity below threshold"
    )

    print(
        "Access Denied"
    )

    return

if not student_email:

    print(
        "\nEmail missing in student record"
    )

    return

print(
    "\nFace Verified"
)

print(
    "Generating OTP..."
)

issue_otp(
    student_id,
    student_email,
    student_name
)

print(
    f"OTP sent to {student_email}"
)

entered_otp = input(
    "\nEnter OTP: "
).strip()

entered_hash = hash_otp(
    entered_otp
)

if not verify_otp(
    student_id,
    entered_hash
):

    print(
        "\nInvalid OTP"
    )

    print(
        "Attendance Not Marked"
    )

    return

if was_marked_recently(
    student_id,
    minutes=5
):

    print(
        "\nAttendance already marked recently"
    )

    return

record_attendance(
    student_id=student_id,
    name=student_name,
    email=student_email,
    confidence=similarity
)

attended = get_student_attendance(
    student_id
)

total = get_total_classes()

if total == 0:
    total = 1

percentage = (
    attended / total
) * 100

send_attendance_report(
    student_email,
    student_name,
    attended,
    total,
    percentage
)

print(
    "\nAttendance Marked Successfully"
)

print(
    f"Student : {student_name}"
)

print(
    f"Score   : {similarity:.4f}"
)

print(
    f"Attendance : {percentage:.2f}%"
)

print(
    "Attendance summary email sent."
)
```

if **name** == "**main**":
main()

