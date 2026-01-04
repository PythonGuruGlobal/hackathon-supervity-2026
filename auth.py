"""
JWT Authentication System
=========================
Handles JWT token generation, validation, and user authentication.
"""

import jwt
import datetime
from functools import wraps
from flask import request, jsonify
from typing import Optional, Dict, Callable
import os


# JWT Configuration
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = 'HS256'
TOKEN_EXPIRY_HOURS = 24


class JWTAuth:
    """JWT Authentication handler."""
    
    @staticmethod
    def generate_token(user_id: int, username: str, email: str) -> str:
        """Generate JWT token for user."""
        payload = {
            'user_id': user_id,
            'username': username,
            'email': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRY_HOURS),
            'iat': datetime.datetime.utcnow()
        }
        
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict]:
        """Decode and validate JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def get_token_from_header() -> Optional[str]:
        """Extract token from Authorization header."""
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]
        return None


def token_required(f: Callable) -> Callable:
    """
    Decorator to protect routes with JWT authentication.
    
    Usage:
        @app.route('/api/protected')
        @token_required
        def protected_route(current_user):
            return {'message': 'Access granted', 'user': current_user}
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = JWTAuth.get_token_from_header()
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'Token is missing',
                'message': 'Please provide a valid authentication token'
            }), 401
        
        try:
            payload = JWTAuth.decode_token(token)
            if not payload:
                return jsonify({
                    'success': False,
                    'error': 'Token is invalid or expired',
                    'message': 'Please log in again'
                }), 401
            
            # Pass user info to the route
            current_user = {
                'user_id': payload['user_id'],
                'username': payload['username'],
                'email': payload['email']
            }
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': 'Token validation failed',
                'message': str(e)
            }), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated


def optional_token(f: Callable) -> Callable:
    """
    Decorator for routes that work with or without authentication.
    If token is provided, user info is passed. Otherwise, None is passed.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = JWTAuth.get_token_from_header()
        current_user = None
        
        if token:
            try:
                payload = JWTAuth.decode_token(token)
                if payload:
                    current_user = {
                        'user_id': payload['user_id'],
                        'username': payload['username'],
                        'email': payload['email']
                    }
            except:
                pass
        
        return f(current_user, *args, **kwargs)
    
    return decorated


if __name__ == "__main__":
    # Test JWT generation and validation
    print("🔐 Testing JWT Authentication\n")
    
    # Generate token
    token = JWTAuth.generate_token(1, "test_user", "test@example.com")
    print(f"✅ Generated Token: {token[:50]}...\n")
    
    # Decode token
    payload = JWTAuth.decode_token(token)
    if payload:
        print(f"✅ Token Valid!")
        print(f"   User ID: {payload['user_id']}")
        print(f"   Username: {payload['username']}")
        print(f"   Expires: {datetime.datetime.fromtimestamp(payload['exp'])}")
    
    print("\n✅ JWT Authentication ready!")
