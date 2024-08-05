from functools import wraps
from flask import request, jsonify
import os


def require_custom_authentication(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the custom header and secret code
        custom_header = request.headers.get('X-YTAPI-Secret')
        secret_code = os.environ.get('SECRET_CODE')

        # Check if the header is present and matches the secret code
        if custom_header != secret_code:
            return jsonify({"error": "Unauthorized"}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function