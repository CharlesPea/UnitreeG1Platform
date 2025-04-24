# gauge_app/routes/video_routes.py

from flask import Blueprint, Response
from gauge_app.services.camera_service import gen_frames, gen_raw_frames

bp = Blueprint('video', __name__)

@bp.route('/video_feed')
def video_feed():
    return Response(
        gen_frames(), 
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@bp.route('/video_raw')
def video_raw():
    return Response(
        gen_raw_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )
