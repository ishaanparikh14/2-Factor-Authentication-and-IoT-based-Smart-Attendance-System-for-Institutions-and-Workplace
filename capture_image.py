'''import cv2
import os

SAVE_DIR = "sample_images"

os.makedirs(SAVE_DIR, exist_ok=True)

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

if not cap.isOpened():
    print("Cannot open webcam")
    exit()

print("\nPress 's' to save image")
print("Press 'q' to quit\n")

count = 1

while True:

    ret, frame = cap.read()

    if not ret:
        print("Failed to capture frame")
        break

    cv2.imshow("Capture Face", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('s'):

        filename = os.path.join(
            SAVE_DIR,
            f"face_{count}.jpg"
        )

        cv2.imwrite(filename, frame)

        print(f"Saved: {filename}")

        count += 1

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()'''

import cv2

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Cannot open camera")
    exit()

print("Press S to save image")
print("Press Q to quit")

count = 1

while True:

    ret, frame = cap.read()

    if not ret:
        continue

    cv2.imshow(
        "Face Capture",
        frame
    )

    key = cv2.waitKey(1) & 0xFF

    if key == ord('s'):

        filename = f"face_{count}.jpg"

        cv2.imwrite(
            filename,
            frame
        )

        print(
            f"Saved: {filename}"
        )

        count += 1

    elif key == ord('q'):

        break

cap.release()

cv2.destroyAllWindows()
