from flask import Blueprint, Response, current_app
from gauge_app.services.camera_service import gen_frames, gen_raw_frames

bp = Blueprint('video', __name__)  # Make sure this name is unique

@bp.route('/video_feed')
def video_feed():
    return Response(gen_frames(current_app),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@bp.route('/video_raw')
def video_raw():
    """Raw camera feed (no processing)."""
    return Response(
        gen_raw_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )