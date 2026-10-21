import sys
import os
from urllib.parse import parse_qs

# Add root and backend to python path for package resolution
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(root_dir, 'backend')

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.app import app as flask_app

class VercelPathMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        qs = environ.get('QUERY_STRING', '')
        params = parse_qs(qs)
        
        # 1. Check query string ?path= (from vercel.json rewrite)
        if 'path' in params and params['path']:
            subpath = params['path'][0]
            if not subpath.startswith('/'):
                subpath = '/' + subpath
            environ['PATH_INFO'] = '/api' + subpath
        # 2. Check Vercel original matched path header
        elif environ.get('HTTP_X_MATCHED_PATH'):
            environ['PATH_INFO'] = environ['HTTP_X_MATCHED_PATH']
        elif environ.get('HTTP_X_FORWARDED_URI'):
            environ['PATH_INFO'] = environ['HTTP_X_FORWARDED_URI']
            
        return self.wsgi_app(environ, start_response)

app = VercelPathMiddleware(flask_app)
