"""
Vercel Serverless Function 핸들러
이 파일은 Vercel 서버리스 환경에서 Flask 앱을 실행하기 위한 진입점입니다.
"""
from http.server import BaseHTTPRequestHandler
import json
import logging
import traceback
import sys
import os

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vercel_handler")

# Flask 앱 임포트
try:
    # 상대 경로 임포트 시도
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from api.index import app
    logger.info("Flask 앱 임포트 성공 (api.index)")
except ImportError as e:
    logger.error(f"api.index에서 임포트 실패: {e}")
    try:
        # 다른 경로 시도
        from index import app
        logger.info("Flask 앱 임포트 성공 (index)")
    except ImportError as e:
        logger.error(f"index에서 임포트 실패: {e}")
        logger.error(traceback.format_exc())
        # 앱 임포트 실패 시 더미 앱 생성
        from flask import Flask
        app = Flask(__name__)
        
        @app.route('/')
        def error_home():
            return json.dumps({"error": "앱 초기화 실패"})

# Vercel 서버리스 함수 핸들러
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response_data = {
            "status": "healthy",
            "message": "Vercel Flask 서버가 작동 중입니다.",
            "path": self.path
        }
        
        self.wfile.write(json.dumps(response_data).encode())
        return

# WSGI 애플리케이션 함수
def application(environ, start_response):
    """WSGI 애플리케이션 함수"""
    try:
        logger.info(f"WSGI 요청: {environ.get('PATH_INFO', '/')}")
        return app(environ, start_response)
    except Exception as e:
        logger.error(f"WSGI 앱 실행 오류: {e}")
        logger.error(traceback.format_exc())
        status = '500 Internal Server Error'
        response_headers = [('Content-type', 'application/json')]
        start_response(status, response_headers)
        return [json.dumps({"error": str(e)}).encode()]

# Vercel에서 사용하는 진입점
def handler(event, context):
    """Vercel 서버리스 함수 진입점"""
    try:
        logger.info("Vercel 핸들러 호출됨")
        
        # Flask 앱 실행
        return app
    except Exception as e:
        logger.error(f"핸들러 실행 오류: {e}")
        logger.error(traceback.format_exc())
        # 오류 발생 시 JSON 응답 반환
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
            "headers": {"Content-Type": "application/json"}
        } 