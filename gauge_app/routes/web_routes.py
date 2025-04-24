from flask import Blueprint, send_from_directory, current_app

bp = Blueprint('web', __name__)

@bp.route('/', defaults={'path': ''})
@bp.route('/<path:path>')
def serve(path):
    return send_from_directory(current_app.static_folder, 'index.html')