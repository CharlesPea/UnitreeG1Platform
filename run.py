import sys
import os

# Add the current directory to Python's path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from gauge_app.app import app, socketio

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3000)