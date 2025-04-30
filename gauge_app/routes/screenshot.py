import base64
import cv2
import openai
from flask import Blueprint, jsonify, current_app
import gauge_app.services.camera_service as camera_service

bp = Blueprint('screenshot', __name__)

@bp.route('/screenshot')
def screenshot():
    try:
        # 1) Check camera
        if camera_service.camera is None:
            return jsonify({'error': 'Camera not initialized'}), 500

        # 2) Capture frame
        success, frame = camera_service.camera.read()
        if not success:
            return jsonify({'error': 'Failed to capture frame'}), 500

        # 3) Downscale & compress for fewer tokens
        h, w = frame.shape[:2]
        scale = 256.0 / max(h, w)
        small = cv2.resize(frame, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)
        ret, buf = cv2.imencode('.jpg', small, [cv2.IMWRITE_JPEG_QUALITY, 30])
        if not ret:
            return jsonify({'error': 'Failed to encode image'}), 500

        # 4) Base64-encode
        img_b64 = base64.b64encode(buf.tobytes()).decode('utf-8')

        # 5) Prepare and call ChatGPT
        openai.api_key = current_app.config.get('OPENAI_API_KEY')
        if not openai.api_key:
            return jsonify({'error': 'OPENAI_API_KEY not set in config'}), 500

        system_prompt = (
            "You are a remote-operated humanoid. "
            "Describe this image in one sentence, prioritizing any analog and digital meters you see. "
            "If you see a meter, say: \u201cMeter: <value>/<scale>. Other: <list>.\u201d "
            "If you don't see a meter check again and really make sure it is there"
            "Otherwise: \u201cNo meters found. Objects: <LIST THE OBJECTS YOU SEE>.\u201d"
        )

        resp = openai.ChatCompletion.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': img_b64}
            ]
        )

        # 6) Extract and return the answer
        answer = resp.choices[0].message.content or ""
        return jsonify({'response': answer.strip()}), 200

    except Exception as e:
        # Catch-all ensures JSON
        return jsonify({'error': str(e)}), 500
