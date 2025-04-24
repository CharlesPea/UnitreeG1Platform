# gauge_app/services/camera_service.py
import cv2
import numpy as np
from gauge_app.utils.gauge_utils import (
    findRed, findCircles, read_regular_gauge, getNeedleMask
)

# OpenCV Camera setup
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def gen_frames(app):
    """Generate video frames with gauge detection overlay."""
    while True:
        success, frame = camera.read()
        if not success:
            break

        # Get mask and gauge data
        mask = getNeedleMask(frame)
        circles = findCircles(mask)

        # Draw a border around the first detected gauge
        if circles:
            x, y, r = circles[0]
            cv2.circle(frame, (x, y), r, (0, 0, 255), 3)

        # Compute the reading and overlay text
        val = read_regular_gauge(frame)
        app.latest_gauge_value = val
        text = f"Gauge: {val if val is not None else '--'}%"
        cv2.putText(frame, text, (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                   (0, 255, 0), 3)

        # Encode & yield
        ret, buf = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        jpg = buf.tobytes()
        yield (b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n')

def gen_raw_frames():
    """Just grab & stream the raw BGR camera frames as JPEGs."""
    while True:
        success, frame = camera.read()
        if not success:
            break
        ret, buf = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        jpg = buf.tobytes()
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n'
        )