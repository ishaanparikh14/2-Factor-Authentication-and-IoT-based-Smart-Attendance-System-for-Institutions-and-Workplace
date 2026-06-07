from firebase_admin import firestore
from firebase_manager import db

def sync_attendance(student_id, name, email, confidence, attended,total,percentage):
    db.collection("students").document(student_id).set(
        {
            "student_id": student_id,
            "name": name,
            "email": email,
            "attendance_count": attended
        },
        merge=True
    )

    db.collection("attendance_logs").add(
        {
            "student_id": student_id,
            "name": name,
            "email": email,
            "confidence": confidence,
            "timestamp": firestore.SERVER_TIMESTAMP
        }
    )

    print("Firebase sync successful")
