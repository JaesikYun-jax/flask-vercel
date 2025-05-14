"""
Vercel 서버리스 함수 핸들러
"""
import json
import traceback
from io import BytesIO
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

def handler(event, context):
    """
    Vercel 서버리스 함수 핸들러
    이것이 Vercel 서버리스 함수의 진입점입니다.
    """
    try:
        # Vercel 이벤트 데이터에서 필요한 정보 추출
        path = event.get('path', '/')
        http_method = event.get('httpMethod', 'GET')
        headers = event.get('headers', {})
        query_params = event.get('queryStringParameters', {})
        body = event.get('body', '')
        
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
        result = app(environ, start_response)
        response_data.extend([chunk.decode('utf-8') if isinstance(chunk, bytes) else chunk for chunk in result])
        
        # CORS 헤더 추가
        response_headers[0]['Access-Control-Allow-Origin'] = '*'
        response_headers[0]['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response_headers[0]['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        
        # Vercel 형식으로 응답 반환
        return {
            'statusCode': status_code[0],
            'headers': response_headers[0],
            'body': ''.join(response_data)
        }
        
    except Exception as e:
        # 오류 발생 시 처리
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            })
        } 