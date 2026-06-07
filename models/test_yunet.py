import cv2

detector = cv2.FaceDetectorYN.create(
    "yunet.onnx",
    "",
    (320, 320)
)

print("YuNet loaded successfully")
