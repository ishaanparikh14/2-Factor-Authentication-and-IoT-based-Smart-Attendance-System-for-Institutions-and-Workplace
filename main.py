import time
import cv2
import RPi.GPIO as GPIO
import sys
import select
# Ensure all these files are in the same folder!
from firebase_sync import sync_attendance

# NOTE: You must ensure `detect_faces` is available in your face_pipeline to count the faces!
from face_pipeline import detect_faces, detect_best_face, align_face, get_embedding
from qdrant_manager import search_embedding
from otp_service import issue_otp, hash_otp
from email_service import send_attendance_report
from config import FACE_MATCH_THRESHOLD

from attendance_db import (
    init_db,
    verify_otp,
    record_attendance,
    was_marked_recently,
    get_student_attendance,
    is_otp_verified,
    get_total_classes
)

# ==========================================
# GPIO PIN CONFIGURATION
# ==========================================

IR_PIN = 17
GREEN_LED = 23
RED_LED = 24
BUZZER = 18

# Suppress the "channel is already in use" warnings
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(IR_PIN, GPIO.IN)
GPIO.setup(GREEN_LED, GPIO.OUT)
GPIO.setup(RED_LED, GPIO.OUT)
GPIO.setup(BUZZER, GPIO.OUT)

# Ensure everything is off on startup
GPIO.output(GREEN_LED, GPIO.LOW)
GPIO.output(RED_LED, GPIO.LOW)
GPIO.output(BUZZER, GPIO.LOW)

# ==========================================
# HARDWARE HELPER FUNCTIONS
# ==========================================

def all_off():
    GPIO.output(GREEN_LED, GPIO.LOW)
    GPIO.output(RED_LED, GPIO.LOW)
    GPIO.output(BUZZER, GPIO.LOW)

def green_success(message="ATTENDANCE VERIFIED"):
    """Flashes green LED and buzzes for success."""
    GPIO.output(RED_LED, GPIO.LOW)
    GPIO.output(GREEN_LED, GPIO.HIGH)
    print(message)
    
    GPIO.output(BUZZER, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(BUZZER, GPIO.LOW)

def red_error():
    """Flashes red LED and buzzes for failure."""
    GPIO.output(GREEN_LED, GPIO.LOW)
    GPIO.output(RED_LED, GPIO.HIGH)
    
    GPIO.output(BUZZER, GPIO.HIGH)
    time.sleep(2.5)
    GPIO.output(BUZZER, GPIO.LOW)

def multiple_faces_warning():
    """Triggers 2 beeps and shifts LED from Red to Green 2 times."""
    print("\n[WARNING] Multiple faces detected! Please stand alone.")
    
    for _ in range(2):
        # Shift 1: Red ON, Green OFF, Buzzer ON (Beep)
        GPIO.output(RED_LED, GPIO.HIGH)
        GPIO.output(GREEN_LED, GPIO.LOW)
        GPIO.output(BUZZER, GPIO.HIGH)
        time.sleep(0.3)
        
        # Shift 2: Green ON, Red OFF, Buzzer OFF
        GPIO.output(RED_LED, GPIO.LOW)
        GPIO.output(GREEN_LED, GPIO.HIGH)
        GPIO.output(BUZZER, GPIO.LOW)
        time.sleep(0.3)
        
    all_off()

def capture_frame():
    """Activates the camera and returns the final frame captured."""
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

    if not cap.isOpened():
        print("Cannot open camera")
        return None

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("\nCamera activated. Showing live feed for 10 seconds...")
    start_time = time.time()
    last_frame = None
    CAMERA_PREVIEW_TIME = 5

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

# ==========================================
# CORE FACE PROCESSING LOGIC
# ==========================================

def process_face(frame):
    # 1. Count faces first to enforce rules
    faces = detect_faces(frame)
    
    if faces is None or len(faces) == 0:
        print("\nNot marked. No single face could be found in the allotted time. Please retry.")
        red_error()
        return
        
    if len(faces) > 1:
        multiple_faces_warning()
        return

    # 2. Extract the best/only face safely
    face_info = detect_best_face(frame)
    if face_info is None:
        print("\nNot marked. No single face could be found in the allotted time. Please retry.")
        red_error()
        return

    aligned = align_face(frame, face_info["landmarks"])
    embedding = get_embedding(aligned)

    # 3. Search Database
    print("Searching Qdrant database...")
    results = search_embedding(embedding, limit=1)

    if len(results) == 0:
        print("Unknown person")
        print("ACCESS DENIED")
        red_error()
        return

    best = results[0]
    similarity = float(best.score)
    payload = best.payload

    if similarity < FACE_MATCH_THRESHOLD:
        print(f"Face not recognized (score={similarity:.4f})")
        print("ACCESS DENIED")
        red_error()
        return

    # 4. Match Found - Extract Data
    student_id = payload["student_id"]
    student_name = payload["name"]
    student_email = payload["email"]
    print("\nMATCH FOUND")
    print(f"Student: {student_name} | ID: {student_id} | Score: {similarity:.4f}")

    # 5. OTP Verification
    print("\nSending OTP...")
    issue_otp(student_id, student_email, student_name)
    
    print(f"\nOTP sent to {student_email}")
    print("Waiting for OTP (Timeout in 60s)...")
    print("-> Enter OTP on your phone OR type it here and press Enter: ", end="", flush=True)

    start_time = time.time()
    otp_success = False

    # Loop for 60 seconds looking for an answer
    while time.time() - start_time < 60:
        
        # Method A: Check if the Web App solved it in the database
        if is_otp_verified(student_id):
            print("\n\n[SUCCESS] OTP verified via Phone Web App!")
            otp_success = True
            break
            
        # Method B: Check if someone typed something in the terminal (Non-blocking)
        # The '0.5' means it waits half a second for keyboard input before looping back to check the DB
        i, o, e = select.select([sys.stdin], [], [], 0.5)
        if i:
            entered_otp = sys.stdin.readline().strip()
            if entered_otp:
                entered_hash = hash_otp(entered_otp)
                if verify_otp(student_id, entered_hash):
                    print("\n[SUCCESS] OTP verified via Terminal!")
                    otp_success = True
                    break
                else:
                    print("\n[ERROR] Incorrect OTP. Try again: ", end="", flush=True)

    if not otp_success:
        print("\n\n[TIMEOUT] No valid OTP entered in time. Please rescan face.")
        red_error()
        return

    # 6. Check Cooldown (Prevents database spam if same face is scanned twice)
   # if was_marked_recently(student_id):
    #    green_success("\nAccess Granted: Attendance already marked recently")
     #   return

    # 7. Record to local SQLite
    record_attendance(
        student_id=student_id,
        name=student_name,
        email=student_email,
        confidence=similarity
    )

    # 8. Fetch updated counts from SQLite
    attended = get_student_attendance(student_id)
    total = get_total_classes()
    percentage = (attended / total*100) if total > 0 else 0   
    print(f"DEBUG: Local DB updated. Total attended: {attended}.(Percentage : {attended}/{total}) Syncing to Cloud...")

    # 9. Sync to Firebase Cloud
    sync_attendance(
        student_id,
        student_name,
        student_email,
        similarity,
        attended,
        total,
        percentage
    )

    # 10. Send Email Notification
    send_attendance_report(
        student_email,
        student_name,
        attended,
        total,
        percentage
    )

    # 11. Final Success Indicator
    green_success("\nATTENDANCE VERIFIED AND SYNCED TO FIREBASE!")

# ==========================================
# MAIN EXECUTION LOOP
# ==========================================

if __name__ == "__main__":
    try:
        init_db()
        print("\nSystem Ready")
        print("Waiting for IR trigger...\n")

        while True:
            # IR Sensor Trigger (OBJECT DETECTED => GPIO LOW)
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
        print("\nStopping system gracefully...")

    finally:
        all_off()
        GPIO.cleanup()
