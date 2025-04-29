import base64, json, cv2, openai
from flask import Blueprint, jsonify, current_app
from gauge_app.services.camera_service import camera

bp = Blueprint('screenshot', __name__)

@bp.route('/screenshot')
def screenshot():
    if camera is None:
        return jsonify({'error': 'Camera not initialized'}), 500

    success, frame = camera.read()
    if not success:
        return jsonify({'error': 'Failed to capture frame'}), 500

    ret, buf = cv2.imencode('.jpg', frame)
    if not ret:
        return jsonify({'error': 'Failed to encode image'}), 500

    img_b64 = base64.b64encode(buf.tobytes()).decode('utf-8')

    # Call ChatGPT
    openai.api_key = current_app.config['OPENAI_API_KEY']
    try:
        resp = openai.ChatCompletion.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'system',
                 'content': 'You are an image analysis assistant.'},
                {'role': 'user',
                 'content': 'Please analyze this image.'}
            ],
            function_call={
                'name': 'analyze_image',
                'arguments': json.dumps({'image_base64': img_b64})
            },
            functions=[{
                'name': 'analyze_image',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'image_base64': {
                            'type': 'string',
                            'description': 'Base64-encoded JPEG'
                        }
                    },
                    'required': ['image_base64']
                }
            }]
        )
        # Extract assistant reply
        answer = resp.choices[0].message.content
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'response': answer})
