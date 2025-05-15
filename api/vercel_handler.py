"""
Vercel 서버리스 함수 핸들러
"""
import json
import traceback
import logging
import time
import os
import sys
from io import BytesIO
from flask import Flask

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 플래스크 앱 임포트
try:
    from api.index import app
    logger.info("API 앱 모듈에서 로드 성공")
except ImportError:
    try:
        from index import app
        logger.info("현재 디렉토리에서 앱 로드 성공")
    except ImportError:
        logger.error("앱 임포트 실패, 기본 앱 생성")
        app = Flask(__name__)
        
        @app.route('/')
        def error_home():
            return json.dumps({
                "success": False,
                "error": "앱 초기화 실패",
                "message": "애플리케이션을 로드하는 중 오류가 발생했습니다.",
                "timestamp": int(time.time())
            })

def handler(event, context):
    """
    Vercel 서버리스 함수 핸들러
    이것이 Vercel 서버리스 함수의 진입점입니다.
    """
    start_time = time.time()
    logger.info(f"요청 시작: {event.get('path', '/')} [{event.get('httpMethod', 'GET')}]")
    
    try:
        # Vercel 이벤트 데이터에서 필요한 정보 추출
        path = event.get('path', '/')
        http_method = event.get('httpMethod', 'GET')
        headers = event.get('headers', {})
        query_params = event.get('queryStringParameters', {})
        body = event.get('body', '')
        
        # 요청 정보 로깅
        logger.info(f"요청 경로: {path}, 메소드: {http_method}")
        if query_params:
            logger.info(f"쿼리 파라미터: {query_params}")
        
        # OPTIONS 요청 빠른 처리 (CORS preflight)
        if http_method == 'OPTIONS':
            logger.info("OPTIONS 요청 처리")
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With'
                },
                'body': ''
            }
        
        # 환경 변수 설정
        environ = {
            'REQUEST_METHOD': http_method,
            'PATH_INFO': path,
            'QUERY_STRING': '&'.join([f"{k}={v}" for k, v in query_params.items()]) if query_params else '',
            'CONTENT_TYPE': headers.get('content-type', ''),
            'CONTENT_LENGTH': str(len(body) if body else 0),
            'wsgi.input': BytesIO(body.encode() if body else b''),
            'wsgi.errors': BytesIO(),
            'wsgi.version': (1, 0),
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
            'wsgi.url_scheme': 'https',
            'SERVER_NAME': 'vercel',
            'SERVER_PORT': '443',
            'REMOTE_ADDR': headers.get('x-real-ip', headers.get('x-forwarded-for', '127.0.0.1')),
            'VERCEL_DEPLOYMENT_ID': os.environ.get('VERCEL_DEPLOYMENT_ID', 'local'),
            'VERCEL_ENV': os.environ.get('VERCEL_ENV', 'development')
        }
        
        # 요청 헤더 추가
        for header, value in headers.items():
            key = 'HTTP_' + header.upper().replace('-', '_')
            environ[key] = value
            
        # WSGI 응답을 수집하기 위한 변수들
        response_data = []
        status_code = [200]
        response_headers = [{}]
        
        def start_response(status, response_headers_list, exc_info=None):
            status_code[0] = int(status.split(' ')[0])
            response_headers[0] = dict(response_headers_list)
            return lambda x: response_data.append(x)
        
        # Flask 앱 호출
        logger.info("Flask 앱 실행")
        result = app(environ, start_response)
        response_data.extend([chunk.decode('utf-8') if isinstance(chunk, bytes) else chunk for chunk in result])
        
        # CORS 헤더 추가
        response_headers[0]['Access-Control-Allow-Origin'] = '*'
        response_headers[0]['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response_headers[0]['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        
        # 응답 시간 계산
        elapsed_time = round((time.time() - start_time) * 1000, 2)
        logger.info(f"응답 생성 완료: {status_code[0]}, 소요 시간: {elapsed_time}ms")
        
        # Vercel 형식으로 응답 반환
        return {
            'statusCode': status_code[0],
            'headers': response_headers[0],
            'body': ''.join(response_data)
        }
        
    except Exception as e:
        # 오류 발생 시 처리
        elapsed_time = round((time.time() - start_time) * 1000, 2)
        error_detail = traceback.format_exc()
        logger.error(f"핸들러 오류 발생: {str(e)}")
        logger.error(f"상세 오류: {error_detail}")
        logger.error(f"요청 처리 실패, 소요 시간: {elapsed_time}ms")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS'
            },
            'body': json.dumps({
                'success': False,
                'message': '서버 내부 오류가 발생했습니다.',
                'error': str(e),
                'timestamp': int(time.time()),
                'path': event.get('path', '/'),
                'method': event.get('httpMethod', 'GET')
                # 프로덕션 환경에서는 보안을 위해 스택 트레이스를 노출하지 않는 것이 좋습니다
                # 'traceback': error_detail if os.environ.get('ENV') == 'development' else None
            })
        } 