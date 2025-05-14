"""
AI 추측 게임 API 서버
"""
import os
import json
import logging
import platform
import sys
from flask import Flask, request, jsonify
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask 앱 초기화
app = Flask(__name__)

# CORS 처리 함수
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    return response

# CORS 헤더 추가
@app.after_request
def after_request(response):
    return add_cors_headers(response)

# CORS Preflight 요청 처리
@app.route('/', methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path=""):
    return "", 200

# API 기본 경로
@app.route('/')
def home():
    """기본 경로 처리"""
    return jsonify({
        "status": "online",
        "message": "AI 추측 게임 API 서버 작동 중",
        "version": "1.0.0"
    })

# 헬스 체크 API
@app.route('/api/health')
def health_check():
    """API 서버 상태 확인"""
    return jsonify({
        "status": "online",
        "message": "API 서버가 정상 작동 중입니다."
    })

# 게임 목록 API
@app.route('/api/games')
def list_games():
    """게임 목록 반환"""
    try:
        # 예시 게임 아이템
        games = [
            {
                "id": "1",
                "title": "신비한 인물 찾기",
                "category": "인물",
                "character_name": "알 수 없는 인물",
                "max_turns": 10
            }
        ]
        return jsonify({
            "success": True,
            "data": games
        })
    except Exception as e:
        logger.error(f"게임 목록 조회 에러: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 디버그 정보 API
@app.route('/api/debug')
def debug_info():
    """디버깅 정보 반환"""
    try:
        debug_data = {
            "python_version": sys.version,
            "platform": platform.platform(),
            "environment": {k: v for k, v in os.environ.items() if not k.startswith('AWS_') and not 'SECRET' in k.upper() and not 'KEY' in k.upper()},
            "cwd": os.getcwd(),
            "files_in_api": os.listdir(os.path.dirname(__file__)) if os.path.exists(os.path.dirname(__file__)) else [],
            "request_headers": dict(request.headers),
            "request_url": request.url,
            "request_method": request.method
        }
        return jsonify({
            "success": True,
            "data": debug_data
        })
    except Exception as e:
        logger.error(f"디버그 정보 생성 에러: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 로컬 개발용
if __name__ == '__main__':
    app.run(debug=True)

def handle(request, context):
    """
    API 서버 루트 엔드포인트 핸들러
    """
    # CORS 헤더
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Content-Type': 'application/json'
    }
    
    # OPTIONS 요청(CORS preflight) 처리
    if request.get('method', '') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    # 응답 데이터
    response_data = {
        'status': 'online',
        'message': 'AI 추측 게임 API 서버 작동 중',
        'version': '1.0.0'
    }
    
    # 응답 반환
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps(response_data)
    }

# 샘플 게임 데이터
GAMES = [
    {
        "id": "1",
        "title": "신비한 인물 찾기",
        "category": "인물",
        "character_name": "알 수 없는 인물",
        "max_turns": 10
    },
    {
        "id": "2",
        "title": "플러팅 마스터",
        "category": "대화",
        "character_name": "신비한 상대",
        "max_turns": 5
    }
]

class handler(BaseHTTPRequestHandler):
    """
    AI 추측 게임 API 서버 핸들러
    모든 API 경로를 처리합니다.
    """
    
    def send_json_response(self, data, status=200):
        """JSON 응답 전송"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def do_OPTIONS(self):
        """CORS Preflight 요청 처리"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_GET(self):
        """GET 요청 처리"""
        url_parts = urlparse(self.path)
        path = url_parts.path
        
        # 루트 경로
        if path == '/':
            return self.handle_home()
        
        # 헬스 체크 API
        elif path == '/api/health':
            return self.handle_health()
        
        # 게임 목록 API
        elif path == '/api/games':
            return self.handle_games()
        
        # 디버그 정보 API
        elif path == '/api/debug':
            return self.handle_debug()
        
        # 404 오류
        else:
            return self.send_json_response({
                'success': False,
                'error': '요청한 API 경로를 찾을 수 없습니다.'
            }, 404)
    
    def do_POST(self):
        """POST 요청 처리"""
        url_parts = urlparse(self.path)
        path = url_parts.path
        
        # 게임 시작 API
        if path == '/api/start':
            # 요청 본문 읽기
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(body) if body else {}
                return self.handle_start_game(data)
            except json.JSONDecodeError:
                return self.send_json_response({
                    'success': False,
                    'error': '유효하지 않은 JSON 데이터'
                }, 400)
        
        # 질문 API
        elif path == '/api/ask':
            # 요청 본문 읽기
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(body) if body else {}
                return self.handle_ask(data)
            except json.JSONDecodeError:
                return self.send_json_response({
                    'success': False,
                    'error': '유효하지 않은 JSON 데이터'
                }, 400)
        
        # 게임 종료 API
        elif path == '/api/end':
            # 요청 본문 읽기
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(body) if body else {}
                return self.handle_end_game(data)
            except json.JSONDecodeError:
                return self.send_json_response({
                    'success': False,
                    'error': '유효하지 않은 JSON 데이터'
                }, 400)
        
        # 404 오류
        else:
            return self.send_json_response({
                'success': False,
                'error': '요청한 API 경로를 찾을 수 없습니다.'
            }, 404)
    
    # API 핸들러 메소드
    def handle_home(self):
        """홈 경로 처리"""
        return self.send_json_response({
            'status': 'online',
            'message': 'AI 추측 게임 API 서버 작동 중',
            'version': '1.0.0'
        })
    
    def handle_health(self):
        """헬스 체크 처리"""
        return self.send_json_response({
            'status': 'online',
            'message': 'API 서버가 정상 작동 중입니다.'
        })
    
    def handle_games(self):
        """게임 목록 처리"""
        return self.send_json_response({
            'success': True,
            'data': GAMES
        })
    
    def handle_debug(self):
        """디버그 정보 처리"""
        try:
            debug_info = {
                'python_version': sys.version,
                'platform': platform.platform(),
                'env_vars': {k: v for k, v in os.environ.items() 
                            if not k.startswith('AWS_') 
                            and not 'SECRET' in k.upper() 
                            and not 'KEY' in k.upper()},
                'request_info': {
                    'method': self.command,
                    'path': self.path,
                    'headers': dict(self.headers),
                },
            }
            
            # 파일 시스템 정보 수집 시도
            try:
                debug_info['current_dir'] = os.getcwd()
                debug_info['dir_listing'] = os.listdir('.')
                if os.path.exists('./api'):
                    debug_info['api_dir_listing'] = os.listdir('./api')
            except Exception as fs_err:
                debug_info['filesystem_error'] = str(fs_err)
            
            return self.send_json_response({
                'success': True,
                'data': debug_info
            })
            
        except Exception as e:
            return self.send_json_response({
                'success': False,
                'error': str(e)
            }, 500)
    
    def handle_start_game(self, data):
        """게임 시작 처리"""
        # 간단한 게임 시작 구현 (예시)
        game_id = f"game_{os.urandom(4).hex()}"
        
        return self.send_json_response({
            'success': True,
            'data': {
                'game_id': game_id,
                'message': '게임이 시작되었습니다.',
                'turn': 1,
                'max_turns': 10
            }
        })
    
    def handle_ask(self, data):
        """질문 처리"""
        # 간단한 질문 응답 구현 (예시)
        game_id = data.get('game_id')
        message = data.get('message')
        
        if not game_id or not message:
            return self.send_json_response({
                'success': False,
                'error': 'game_id와 message가 필요합니다.'
            }, 400)
        
        # 치트키 확인
        if message == '승승리':
            return self.send_json_response({
                'success': True,
                'data': {
                    'game_id': game_id,
                    'message': '축하합니다! 치트키를 사용하여 승리했습니다.',
                    'game_over': True,
                    'win': True
                }
            })
        elif message == '패패배':
            return self.send_json_response({
                'success': True,
                'data': {
                    'game_id': game_id,
                    'message': '치트키를 사용하여 패배했습니다.',
                    'game_over': True,
                    'win': False
                }
            })
        
        # 일반 응답
        return self.send_json_response({
            'success': True,
            'data': {
                'game_id': game_id,
                'message': f'당신의 질문 "{message}"에 대한 응답입니다.',
                'turn': 2,
                'game_over': False
            }
        })
    
    def handle_end_game(self, data):
        """게임 종료 처리"""
        game_id = data.get('game_id')
        
        if not game_id:
            return self.send_json_response({
                'success': False,
                'error': 'game_id가 필요합니다.'
            }, 400)
        
        return self.send_json_response({
            'success': True,
            'data': {
                'game_id': game_id,
                'message': '게임이 종료되었습니다.',
                'summary': '게임 결과 요약'
            }
        }) 