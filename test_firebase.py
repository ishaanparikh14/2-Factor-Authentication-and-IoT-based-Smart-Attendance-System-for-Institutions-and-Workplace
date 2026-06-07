from firebase_manager import db

db.collection(
    "test"
).document(
    "hello"
).set(
    {
        "message": "Firebase Working"
    }
)

print("Success")
