QDRANT_URL="https://943e77c1-1c5c-4f5e-9761-4b32aa4408b1.eu-central-1-0.aws.cloud.qdrant.io"
QDRANT_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6MDgyNDBkMTEtMDQyMS00NzE4LThlNGYtOTRiZmJkYWQwMzY4In0.O7eg6nt77jr9fHAPyCoZ1dv0_XduM0nxAOB0a-WcPh4"
STREAM_URL = "http://192.168.1.100:81/stream"
QDRANT_COLLECTION = "IOT_EL"

DEFAULT_IMAGE_SIZE = (112, 112)

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"

YU_NET_MODEL_PATH = str(MODELS_DIR / "yunet.onnx")
ARCFACE_MODEL_PATH = str(MODELS_DIR / "arcface.onnx")

ENROLL_IMAGE_DIR = str(BASE_DIR / "enrollment_images")
ATTENDANCE_DB_PATH = str(BASE_DIR / "database" / "attendance.db")

FACE_MATCH_THRESHOLD = 0.55
OTP_LENGTH = 6
OTP_VALID_MINUTES = 5

# Gmail API

GMAIL_SENDER = "vikas.karthik06@gmail.com"

GMAIL_CLIENT_SECRET = (
    "/home/pi/.config/gws/client_secret.json"
)

GMAIL_TOKEN_FILE = "token.json"
