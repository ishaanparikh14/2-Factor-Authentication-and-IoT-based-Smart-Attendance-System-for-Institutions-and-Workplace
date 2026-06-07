'''import time
import cv2
import RPi.GPIO as GPIO
from firebase_sync import sync_attendance
from face_pipeline import (
    detect_best_face,
    align_face,
    get_embedding
)

from qdrant_manager import (
    search_embedding
)

from otp_service import (
    issue_otp,
    hash_otp
)

from attendance_db import (
    init_db,
    verify_otp,
    record_attendance,
    was_marked_recently
)

from config import FACE_MATCH_THRESHOLD

# ==========================
# GPIO PINS
# ==========================

IR_PIN = 17
GREEN_LED = 23
RED_LED = 24
BUZZER = 18

GPIO.setmode(GPIO.BCM)

GPIO.setup(IR_PIN, GPIO.IN)

GPIO.setup(GREEN_LED, GPIO.OUT)
GPIO.setup(RED_LED, GPIO.OUT)
GPIO.setup(BUZZER, GPIO.OUT)

GPIO.output(GREEN_LED, GPIO.LOW)
GPIO.output(RED_LED, GPIO.LOW)
GPIO.output(BUZZER, GPIO.LOW)

# ==========================
# HELPER FUNCTIONS
# ==========================

def all_off():
    GPIO.output(GREEN_LED, GPIO.LOW)
    GPIO.output(RED_LED, GPIO.LOW)
    GPIO.output(BUZZER, GPIO.LOW)


def green_success():

    GPIO.output(RED_LED, GPIO.LOW)
    GPIO.output(GREEN_LED, GPIO.HIGH)

    print("ATTENDANCE VERIFIED")

    GPIO.output(BUZZER, GPIO.HIGH)

    time.sleep(0.5)

    GPIO.output(BUZZER, GPIO.LOW)

def red_error():

    GPIO.output(GREEN_LED, GPIO.LOW)
    GPIO.output(RED_LED, GPIO.HIGH)

    print("ACCESS DENIED")

    GPIO.output(BUZZER, GPIO.HIGH)

    time.sleep(2.5)

    GPIO.output(BUZZER, GPIO.LOW)

def capture_frame():

    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

    if not cap.isOpened():
        print("Cannot open camera")
        return None

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("\nCamera activated")
    print("Showing live feed for 5 seconds...")

    start_time = time.time()

    last_frame = None
    CAMERA_PREVIEW_TIME=10
    while time.time() - start_time <CAMERA_PREVIEW_TIME :

        ret, frame = cap.read()

        if not ret:
            continue

        last_frame = frame.copy()

        remaining = CAMERA_PREVIEW_TIME - int(time.time() - start_time)

        cv2.putText(
            frame,
            f"Capturing... {remaining}s",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        cv2.imshow(
            "Attendance Camera",
            frame
        )

        cv2.waitKey(1)

    cap.release()

    cv2.destroyAllWindows()

    print("Capture complete")

    return last_frame

# ==========================
# MAIN FACE PROCESSING
# ==========================

def process_face(frame):

    face_info = detect_best_face(frame)

    if face_info is None:

        print("No face detected")

        red_error()

        return

    aligned = align_face(
        frame,
        face_info["landmarks"]
    )

    embedding = get_embedding(
        aligned
    )

    print("Searching database...")

    results = search_embedding(
        embedding,
        limit=1
    )

    if len(results) == 0:

        print("Unknown person")

        red_error()

        return

    best = results[0]

    similarity = float(best.score)

    payload = best.payload

    if similarity <0.65 :

        print(
            f"Face not recognized "
            f"(score={similarity:.4f})"
        )

        red_error()

        return

    student_id = payload["student_id"]
    student_name = payload["name"]
    student_email = payload["email"]

    print("\nMATCH FOUND")
    print("Student:", student_name)
    print("ID:", student_id)
    print("Score:", similarity)

    print("\nSending OTP...")

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

# ... (Previous code) ...
    entered_hash = hash_otp(entered_otp)

    if not verify_otp(student_id, entered_hash):
        print("Incorrect OTP")
        red_error()
        return

    # 1. Check Cooldown First
    if was_marked_recently(student_id):
        print("\nAttendance already marked recently")
        green_success()
        return

    # 2. Record to local SQLite
    record_attendance(
        student_id=student_id,
        name=student_name,
        email=student_email,
        confidence=similarity
    )

    # 3. Fetch updated counts from SQLite
    attended = get_student_attendance(student_id)
    total = get_total_classes()
    if total == 0:
        total = 1

    print("DEBUG: Syncing to Firebase...")
    print(f"Student ID: {student_id} | Attendance Count: {attended}")

    # 4. Sync to Firebase Cloud
    sync_attendance(
        student_id,
        student_name,
        student_email,
        similarity,
        attended,
        total
    )

    # 5. Calculate and Send Email
    percentage = (attended / total) * 100
    send_attendance_report(
        student_email,
        student_name,
        attended,
        total,
        percentage
    )

    # 6. Final Success Notification
    print("\nATTENDANCE VERIFIED AND SYNCED")
    green_success()

# ==========================
# MAIN LOOP
# ==========================
# ... (Rest of your code remains the same)
# ==========================
# MAIN LOOP
# ==========================

try:

    init_db()

    print("\nSystem Ready")
    print("Waiting for IR trigger...\n")

    while True:

        # Your IR test showed:
        # OBJECT DETECTED => GPIO LOW

        if GPIO.input(IR_PIN) == 0:

            print(
                "\nObject detected by IR sensor"
            )

            all_off()

            frame = capture_frame()

            if frame is not None:

                process_face(frame)

            print(
                "\nReturning to standby..."
            )

            time.sleep(3)

        else:

            time.sleep(0.1)

except KeyboardInterrupt:

    print("\nStopping system")

finally:

    all_off()

    GPIO.cleanup()
'''

import time
import cv2
import RPi.GPIO as GPIO

from firebase_sync import sync_attendance
from face_pipeline import detect_best_face, align_face, get_embedding
from qdrant_manager import search_embedding
from otp_service import issue_otp, hash_otp

# Make sure all these are actually in your attendance_db.py!
from attendance_db import (
    init_db,
    verify_otp,
    record_attendance,
    was_marked_recently,
    get_student_attendance,
    get_total_classes
)

# Replace 'email_service' with the actual file name where you put the email function
from email_service import send_attendance_report 
from config import FACE_MATCH_THRESHOLD

# ==========================
# GPIO PINS
# ==========================

IR_PIN = 17
GREEN_LED = 23
RED_LED = 24
BUZZER = 18

GPIO.setmode(GPIO.BCM)
GPIO.setup(IR_PIN, GPIO.IN)
GPIO.setup(GREEN_LED, GPIO.OUT)
GPIO.setup(RED_LED, GPIO.OUT)
GPIO.setup(BUZZER, GPIO.OUT)

GPIO.output(GREEN_LED, GPIO.LOW)
GPIO.output(RED_LED, GPIO.LOW)
GPIO.output(BUZZER, GPIO.LOW)

# ==========================
# HELPER FUNCTIONS
# ==========================

def all_off():
    GPIO.output(GREEN_LED, GPIO.LOW)
    GPIO.output(RED_LED, GPIO.LOW)
    GPIO.output(BUZZER, GPIO.LOW)

def green_success():
    GPIO.output(RED_LED, GPIO.LOW)
    GPIO.output(GREEN_LED, GPIO.HIGH)
    print("ATTENDANCE VERIFIED")
    GPIO.output(BUZZER, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(BUZZER, GPIO.LOW)

def red_error():
    GPIO.output(GREEN_LED, GPIO.LOW)
    GPIO.output(RED_LED, GPIO.HIGH)
    print("ACCESS DENIED")
    GPIO.output(BUZZER, GPIO.HIGH)
    time.sleep(2.5)
    GPIO.output(BUZZER, GPIO.LOW)

def capture_frame():
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

    if not cap.isOpened():
        print("Cannot open camera")
        return None

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("\nCamera activated")
    print("Showing live feed for 10 seconds...")

    start_time = time.time()
    last_frame = None
    CAMERA_PREVIEW_TIME = 10

    while time.time() - start_time < CAMERA_PREVIEW_TIME:
        ret, frame = cap.read()
        if not ret:
            continue

        last_frame = frame.copy()
        remaining = CAMERA_PREVIEW_TIME - int(time.time() - start_time)

        cv2.putText(
            frame,
            f"Capturing... {remaining}s",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )
        cv2.imshow("Attendance Camera", frame)
        cv2.waitKey(1)

    cap.release()
    cv2.destroyAllWindows()
    print("Capture complete")
    return last_frame

# ==========================
# MAIN FACE PROCESSING
# ==========================

def process_face(frame):
    face_info = detect_best_face(frame)

    if face_info is None:
        print("No face detected")
        red_error()
        return

    aligned = align_face(frame, face_info["landmarks"])
    embedding = get_embedding(aligned)

    print("Searching database...")
    results = search_embedding(embedding, limit=1)

    if len(results) == 0:
        print("Unknown person")
        red_error()
        return

    best = results[0]
    similarity = float(best.score)
    payload = best.payload

    # Using the threshold from config, or fallback to 0.65
    if similarity < FACE_MATCH_THRESHOLD:
        print(f"Face not recognized (score={similarity:.4f})")
        red_error()
        return

    student_id = payload["student_id"]
    student_name = payload["name"]
    student_email = payload["email"]

    print("\nMATCH FOUND")
    print("Student:", student_name)
    print("ID:", student_id)
    print("Score:", similarity)

    print("\nSending OTP...")
    issue_otp(student_id, student_email, student_name)
    print(f"OTP sent to {student_email}")

    entered_otp = input("\nEnter OTP: ").strip()
    entered_hash = hash_otp(entered_otp)

    if not verify_otp(student_id, entered_hash):
        print("Incorrect OTP")
        red_error()
        return

    # 1. Check Cooldown First
    #if was_marked_recently(student_id):
    #    print("\nAttendance already marked recently")
    #    green_success()
    #    return

    # 2. Record to local SQLite
    record_attendance(
        student_id=student_id,
        name=student_name,
        email=student_email,
        confidence=similarity
    )

    # 3. Fetch updated counts from SQLite
    attended = get_student_attendance(student_id)
    total = get_total_classes()
    if total == 0:
        total = 1

    print("DEBUG: Syncing to Firebase...")
    print(f"Student ID: {student_id} | Attendance Count: {attended}")

    # 4. Sync to Firebase Cloud
    sync_attendance(
        student_id,
        student_name,
        student_email,
        similarity,
        attended,
        total
    )

    # 5. Calculate and Send Email
    percentage = (attended / total) * 100
    send_attendance_report(
        student_email,
        student_name,
        attended,
        total,
        percentage
    )

    # 6. Final Success Notification
    print("\nATTENDANCE VERIFIED AND SYNCED")
    green_success()

# ==========================
# MAIN LOOP
# ==========================

if __name__ == "__main__":
    try:
        init_db()
        print("\nSystem Ready")
        print("Waiting for IR trigger...\n")

        while True:
            # OBJECT DETECTED => GPIO LOW
            if GPIO.input(IR_PIN) == 0:
                print("\nObject detected by IR sensor")
                all_off()
                
                frame = capture_frame()
                if frame is not None:
                    process_face(frame)
                    
                print("\nReturning to standby...")
                time.sleep(3)
            else:
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping system")

    finally:
        all_off()
        GPIO.cleanup()
