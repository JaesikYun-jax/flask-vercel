"""
AI 추측 게임 API 서버
"""
import os
import json
import logging
import platform
import sys
from flask import Flask, request, jsonify

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Flask 앱 초기화 - 전역 변수로 app 노출
app = Flask(__name__)

# CORS 처리 함수
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    return response

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
        return jsonify({
            "success": True,
            "data": GAMES
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
            "environment": {k: v for k, v in os.environ.items() 
                          if not k.startswith('AWS_') 
                          and not 'SECRET' in k.upper() 
                          and not 'KEY' in k.upper()},
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

# 게임 시작 API
@app.route('/api/start', methods=['POST'])
def start_game():
    """게임 시작"""
    try:
        data = request.get_json(silent=True) or {}
        
        # 간단한 게임 시작 구현 (예시)
        game_id = f"game_{os.urandom(4).hex()}"
        
        return jsonify({
            'success': True,
            'data': {
                'game_id': game_id,
                'message': '게임이 시작되었습니다.',
                'turn': 1,
                'max_turns': 10
            }
        })
    except Exception as e:
        logger.error(f"게임 시작 에러: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 질문 API
@app.route('/api/ask', methods=['POST'])
def ask_question():
    """질문 처리"""
    try:
        data = request.get_json(silent=True) or {}
        game_id = data.get('game_id')
        message = data.get('message')
        
        if not game_id or not message:
            return jsonify({
                'success': False,
                'error': 'game_id와 message가 필요합니다.'
            }), 400
        
        # 치트키 확인
        if message == '승승리':
            return jsonify({
                'success': True,
                'data': {
                    'game_id': game_id,
                    'message': '축하합니다! 치트키를 사용하여 승리했습니다.',
                    'game_over': True,
                    'win': True
                }
            })
        elif message == '패패배':
            return jsonify({
                'success': True,
                'data': {
                    'game_id': game_id,
                    'message': '치트키를 사용하여 패배했습니다.',
                    'game_over': True,
                    'win': False
                }
            })
        
        # 일반 응답
        return jsonify({
            'success': True,
            'data': {
                'game_id': game_id,
                'message': f'당신의 질문 "{message}"에 대한 응답입니다.',
                'turn': 2,
                'game_over': False
            }
        })
    except Exception as e:
        logger.error(f"질문 처리 에러: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 게임 종료 API
@app.route('/api/end', methods=['POST'])
def end_game():
    """게임 종료 처리"""
    try:
        data = request.get_json(silent=True) or {}
        game_id = data.get('game_id')
        
        if not game_id:
            return jsonify({
                'success': False,
                'error': 'game_id가 필요합니다.'
            }), 400
        
        return jsonify({
            'success': True,
            'data': {
                'game_id': game_id,
                'message': '게임이 종료되었습니다.',
                'summary': '게임 결과 요약'
            }
        })
    except Exception as e:
        logger.error(f"게임 종료 에러: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 로컬 개발용
if __name__ == '__main__':
    app.run(debug=True) 