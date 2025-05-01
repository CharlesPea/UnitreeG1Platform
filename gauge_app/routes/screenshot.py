import base64
import cv2
import numpy as np
import openai
from flask import Blueprint, jsonify, current_app
import gauge_app.services.camera_service as camera_service
from datetime import datetime
from gauge_app.services.screenshot_service import screenshot_history

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

        # 3) Preprocess: grayscale, enhance contrast, denoise, sharpen
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        eq = clahe.apply(gray)
        denoised = cv2.bilateralFilter(eq, 9, 75, 75)
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], np.float32)
        sharpened = cv2.filter2D(denoised, -1, kernel)
        processed = cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)

        # 4) Resize for readability but keep token cost low
        h, w = processed.shape[:2]
        target_size = 512.0  # resolution for clarity
        scale = target_size / max(h, w)
        resized = cv2.resize(
            processed,
            (int(w * scale), int(h * scale)),
            interpolation=cv2.INTER_CUBIC
        )

        # 5) JPEG encode at slightly higher quality (70)
        ret, buf = cv2.imencode(
            '.jpg', resized,
            [cv2.IMWRITE_JPEG_QUALITY, 70]
        )
        if not ret:
            return jsonify({'error': 'Failed to encode image'}), 500

        # 6) Base64 and wrap in Markdown image tag
        img_b64 = base64.b64encode(buf).decode('utf-8')
        md_img = f"![meter](data:image/jpeg;base64,{img_b64})"

        # 7) Call GPT-4o-mini
        openai.api_key = current_app.config.get('OPENAI_API_KEY')
        if not openai.api_key:
            return jsonify({'error': 'OPENAI_API_KEY not set'}), 500

        system_prompt = (
            "You are a remote-operated humanoid. "
            "Describe this enhanced image in one sentence, prioritizing any analog and digital meters you see. "
            "If you see a meter, say: “Meter: <value>/<scale>. Other: <list>.” "
            "If you don't see a meter, say: “No meters found. Objects: <LIST THE OBJECTS YOU SEE>.”"
        )

        resp = openai.ChatCompletion.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': md_img}
            ]
        )

        answer = resp.choices[0].message.content.strip()

        # 8) Log with image bytes and response for anomaly report
        screenshot_history.append({
            'time': datetime.now(),
            'image_bytes': buf.tobytes(),
            'response': answer
        })

        # 9) Return the GPT response
        return jsonify({'response': answer}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
