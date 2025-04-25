# gauge_app/services/camera_service.py

import cv2
from flask import current_app
from gauge_app.utils.gauge_utils import (
    getNeedleMask,
    findCircles,
    read_regular_gauge
)

# Camera will be set in init_app()
camera = None

def init_app(app):
    """Initialize the global camera using settings from app.config."""
    global camera
    idx    = app.config['CAMERA_INDEX']
    width  = app.config['CAMERA_WIDTH']
    height = app.config['CAMERA_HEIGHT']

    camera = cv2.VideoCapture(idx)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)


def gen_frames():
    """Stream processed MJPEG frames, overlaying gauge info."""
    if camera is None:
        raise RuntimeError("camera_service not initialized; call init_app(app) first")

    while True:
        success, frame = camera.read()
        if not success:
            break

        # 1) detect needle mask & dial circle
        mask    = getNeedleMask(frame)
        circles = findCircles(mask)

        # 2) overlay dial circle if found
        if circles:
            x, y, r = circles[0]
            cv2.circle(frame, (x, y), r, (0, 0, 255), 3)

        # 3) compute gauge value
        val = read_regular_gauge(frame)
        # store it on the real app object
        current_app.latest_gauge_value = val

        # 4) draw text overlay
        text = f"Gauge: {val if val is not None else '--'}%"
        cv2.putText(frame, text, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                    (0, 255, 0), 3)

        # 5) encode & yield MJPEG
        ret, buf = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        jpg = buf.tobytes()
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n'
        )


def gen_raw_frames():
    """Stream raw MJPEG frames from the camera."""
    if camera is None:
        raise RuntimeError("camera_service not initialized; call init_app(app) first")

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
