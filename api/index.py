import os
import sys

# Add root directory to python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

# Import the existing Flask app from the backend directory
from backend.app import app as flask_app

class StripPrefixMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        if path.startswith('/api'):
            environ['PATH_INFO'] = path[4:] or '/'
        elif path.startswith('/ml-api'):
            environ['PATH_INFO'] = path[7:] or '/'
        return self.wsgi_app(environ, start_response)

# Apply middleware to strip the /api or /ml-api prefix before it reaches Flask
flask_app.wsgi_app = StripPrefixMiddleware(flask_app.wsgi_app)

# Vercel Serverless environment expects an 'app' instance of the Flask app
app = flask_app
