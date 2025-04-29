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


def gen_raw_frames():
    """Stream raw MJPEG frames from the camera."""
    if camera is None:
        raise RuntimeError(
            "camera_service not initialized; call init_app(app) first"
        )

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
            b'Content-Type: image/jpeg\r\n\r\n' 
            + jpg + b'\r\n'
        )
