"""
Vercel 서버리스 함수 핸들러
"""
import json
from flask import Flask

# 플래스크 앱 임포트
try:
    from api.index import app
except ImportError:
    try:
        from index import app
    except ImportError:
        app = Flask(__name__)
        
        @app.route('/')
        def error_home():
            return json.dumps({"error": "앱 초기화 실패"})

def handler(request, context):
    """
    Vercel 서버리스 함수 핸들러
    이것이 Vercel 서버리스 함수의 진입점입니다.
    """
    return app 