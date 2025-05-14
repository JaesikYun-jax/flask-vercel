"""
Vercel Serverless Function 핸들러
이 파일은 Vercel 서버리스 환경에서 Flask 앱을 실행하기 위한 진입점입니다.
"""
import json
import logging
import traceback
import sys
import os
from flask import Flask

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vercel_handler")

# Flask 앱 임포트
try:
    logger.info("Flask 앱 임포트 시도")
    from api.index import app
    logger.info("Flask 앱 임포트 성공 (api.index)")
except ImportError as e:
    logger.error(f"api.index에서 임포트 실패: {e}")
    try:
        from index import app
        logger.info("Flask 앱 임포트 성공 (index)")
    except ImportError as e:
        logger.error(f"index에서 임포트 실패: {e}")
        logger.error(traceback.format_exc())
        # 앱 임포트 실패 시 더미 앱 생성
        app = Flask(__name__)
        
        @app.route('/')
        def error_home():
            return json.dumps({"error": "앱 초기화 실패"})

# Vercel 서버리스 함수를 위한 WSGI 핸들러
def handler(event, context):
    """
    Vercel 서버리스 함수 핸들러 - WSGI 어댑터 역할
    """
    logger.info("Vercel 핸들러 호출됨")
    
    try:
        path = event.get('path', '/')
        http_method = event.get('httpMethod', 'GET')
        headers = event.get('headers', {})
        query_string = event.get('queryStringParameters', {})
        body = event.get('body', '')
        
        logger.info(f"요청 정보: {path} {http_method}")
        
        # 환경 변수 설정
        environ = {
            'REQUEST_METHOD': http_method,
            'PATH_INFO': path,
            'QUERY_STRING': '&'.join([f"{k}={v}" for k, v in query_string.items()]) if query_string else '',
            'CONTENT_TYPE': headers.get('content-type', ''),
            'CONTENT_LENGTH': headers.get('content-length', '0'),
            'SERVER_NAME': 'vercel',
            'SERVER_PORT': '443',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'https',
            'wsgi.input': body,
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
        }
        
        # HTTP 헤더 추가
        for header, value in headers.items():
            key = f"HTTP_{header.upper().replace('-', '_')}"
            environ[key] = value
        
        # WSGI 응답 수집
        response_body = []
        status_code = 200
        response_headers = []
        
        def start_response(status, headers):
            nonlocal status_code, response_headers
            status_parts = status.split(' ', 1)
            status_code = int(status_parts[0])
            response_headers = headers
        
        # Flask 앱을 통한 WSGI 호출
        for chunk in app(environ, start_response):
            if isinstance(chunk, bytes):
                response_body.append(chunk.decode('utf-8'))
            else:
                response_body.append(chunk)
        
        # 응답 본문 조합
        body_content = ''.join(response_body)
        
        # 응답 헤더를 딕셔너리로 변환
        headers_dict = dict(response_headers)
        
        # CORS 헤더 추가
        headers_dict['Access-Control-Allow-Origin'] = '*'
        headers_dict['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
        headers_dict['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
        
        logger.info(f"응답 생성 완료: {status_code}")
        
        # Vercel 형식의 응답 반환
        return {
            'statusCode': status_code,
            'headers': headers_dict,
            'body': body_content
        }
        
    except Exception as e:
        logger.error(f"핸들러 실행 오류: {e}")
        logger.error(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

# 직접 호출 시 테스트 (개발용)
if __name__ == '__main__':
    test_event = {
        'path': '/api/health',
        'httpMethod': 'GET',
        'headers': {},
        'queryStringParameters': {}
    }
    response = handler(test_event, None)
    print(json.dumps(response, indent=2)) 