import base64
import json
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

        # 3) Encode to JPEG
        ret, buf = cv2.imencode('.jpg', frame)
        if not ret:
            return jsonify({'error': 'Failed to encode image'}), 500

        # 4) Base64-encode
        img_b64 = base64.b64encode(buf.tobytes()).decode('utf-8')

        # 5) Prepare and call ChatGPT
        openai.api_key = current_app.config.get('OPENAI_API_KEY')
        if not openai.api_key:
            return jsonify({'error': 'OPENAI_API_KEY not set in config'}), 500

        system_prompt = """
You are a humanoid robot that is being operated remotely and I need you to briefly describe the things you see in the image you received.

I want you to prioritize one object above all and that is any analog meters that you see. Your answers should look as follows:

– If you see a meter:  
  "I see what looks like a meter with a value of 20 over 100, other objects such as x and y are present in this space"

– If you don’t see a meter:  
  "I see x, y and z object in this room, no meters were found"
        """.strip()

        resp = openai.ChatCompletion.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user',
                 'content': f"Here is the image data (base64):\n\n{img_b64}"}
                ]
        )

        # 6) Extract and return the answer
        answer = resp.choices[0].message.content or ""
        return jsonify({'response': answer.strip()}), 200

    except Exception as e:
        # Catch-all to ensure a JSON response
        return jsonify({'error': str(e)}), 500
