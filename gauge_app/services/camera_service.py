# gauge_app/services/camera_service.py

import cv2
from gauge_app.app import app           # <- import the real Flask app
from gauge_app.utils.gauge_utils import (
    getNeedleMask, findCircles, read_regular_gauge
)

# initialize your camera using config values
camera = cv2.VideoCapture(app.config['CAMERA_INDEX'])
camera.set(cv2.CAP_PROP_FRAME_WIDTH,  app.config['CAMERA_WIDTH'])
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, app.config['CAMERA_HEIGHT'])

def gen_frames():
    """Generate video frames with gauge overlay."""
    while True:
        success, frame = camera.read()
        if not success:
            break

        # detect needle and circles
        mask    = getNeedleMask(frame)
        circles = findCircles(mask)

        # overlay circle
        if circles:
            x, y, r = circles[0]
            cv2.circle(frame, (x, y), r, (0, 0, 255), 3)

        # compute and store latest gauge value
        val = read_regular_gauge(frame)
        # now using the real app object, not current_app proxy
        app.latest_gauge_value = val

        # draw the text
        text = f"Gauge: {val if val is not None else '--'}%"
        cv2.putText(frame, text, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                    (0, 255, 0), 3)

        # encode & yield as MJPEG
        ret, buf = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        jpg = buf.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n')

def gen_raw_frames():
    """Just stream the raw frames."""
    while True:
        success, frame = camera.read()
        if not success:
            break
        ret, buf = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        jpg = buf.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n')
