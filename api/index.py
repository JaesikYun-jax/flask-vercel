"""
AI 추측 게임 API 서버 - 간소화 버전
"""
import os
import json
import logging
import time
import random
import sys
import platform
import requests
from flask import Flask, request, jsonify

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask 앱 초기화
app = Flask(__name__)

# 게임 세션 데이터 저장소
GAME_SESSIONS = {}

# OpenAI API 설정
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# 기본 게임 항목
GAMES = [
    {
        "id": 1,
        "title": "플러팅 고수! 전화번호 따기",
        "category": "플러팅",
        "character_name": "윤지혜",
        "character_setting": "당신은 카페에서 우연히 마주친 매력적인 사람입니다. 친절하지만 쉽게 개인정보를 알려주지 않는 성격입니다.",
        "max_turns": 5,
        "win_condition": "상대방의 전화번호를 얻어낸다"
    },
    {
        "id": 2,
        "title": "파티에서 번호 교환하기",
        "category": "플러팅",
        "character_name": "김민준",
        "character_setting": "당신은 친구의 파티에서 만난 사람입니다. 사교적이지만 많은 사람들에게 관심을 받고 있어 쉽게 번호를 주지 않습니다.",
        "max_turns": 4,
        "win_condition": "상대방과 번호를 교환한다"
    },
    {
        "id": 3,
        "title": "꿈의 직장 면접 성공하기",
        "category": "면접",
        "character_name": "박상현",
        "character_setting": "당신은 대기업 면접관입니다. 기술적 지식과 문화적 적합성을 모두 평가하고 있습니다. 인재를 뽑고 싶지만 까다로운 기준이 있습니다.",
        "max_turns": 10,
        "win_condition": "면접관을 설득해 일자리 제안을 받는다"
    }
]

# OpenAI API 호출 함수
def call_openai_api(messages, max_tokens=300):
    """
    OpenAI API 호출 함수
    """
    if not OPENAI_API_KEY:
        logger.warning("OpenAI API 키가 설정되지 않았습니다. 기본 응답을 반환합니다.")
        return "OpenAI API 키가 설정되지 않아 응답을 생성할 수 없습니다."
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        response = requests.post(OPENAI_API_URL, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        else:
            logger.error(f"OpenAI API 오류: {response.status_code} - {response.text}")
            return f"응답을 생성하는 중 오류가 발생했습니다: {response.status_code}"
    
    except Exception as e:
        logger.error(f"OpenAI API 호출 중 예외 발생: {str(e)}")
        return f"응답을 생성하는 중 오류가 발생했습니다: {str(e)}"

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

# 기본 경로
@app.route('/')
def home():
    """기본 경로 처리"""
    return jsonify({
        "status": "online",
        "message": "AI 추측 게임 API 서버 작동 중",
        "version": "1.0.0",
        "timestamp": int(time.time())
    })

# 헬스 체크 API
@app.route('/api/health')
def health_check():
    """API 서버 상태 확인"""
    return jsonify({
        "status": "online",
        "message": "API 서버가 정상 작동 중입니다.",
        "timestamp": int(time.time())
    })

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
            "active_game_sessions": len(GAME_SESSIONS),
            "games_available": len(GAMES),
            "server_time": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "vercel_deployment_id": os.environ.get('VERCEL_DEPLOYMENT_ID', 'local'),
            "openai_api_configured": bool(OPENAI_API_KEY)
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

# 게임 시작 API
@app.route('/api/start', methods=['POST'])
def start_game():
    """게임 시작"""
    try:
        data = request.get_json(silent=True) or {}
        
        # 선택된 게임 ID (선택 사항)
        selected_game_id = data.get('item_id') or data.get('game_id')
        
        # 게임 선택
        if not selected_game_id:
            # 게임 ID가 제공되지 않은 경우 랜덤 선택
            target_game = random.choice(GAMES)
        else:
            # 선택된 ID로 게임 찾기
            try:
                if isinstance(selected_game_id, str) and selected_game_id.isdigit():
                    selected_game_id = int(selected_game_id)
                
                target_game = next((game for game in GAMES if game['id'] == selected_game_id), None)
                
                if not target_game:
                    target_game = random.choice(GAMES)
            except:
                target_game = random.choice(GAMES)
        
        # 게임 ID 생성
        game_id = f"game_{random.randint(10000, 99999)}"
        
        # 게임 정보 생성
        game_info = {
            "game_id": game_id,
            "id": target_game.get('id'),
            "title": target_game.get('title', '알 수 없는 게임'),
            "category": target_game.get('category', '기타'),
            "character_name": target_game.get('character_name', 'AI'),
            "character_setting": target_game.get('character_setting', ''),
            "max_turns": target_game.get('max_turns', 10),
            "current_turn": 1,
            "welcome_message": f"안녕하세요! {target_game.get('character_name', 'AI')}입니다. 게임을 시작합니다."
        }
        
        # 시스템 메시지 생성
        system_message = f"""
당신은 '{target_game.get('title')}' 게임의 '{target_game.get('character_name')}' 역할을 수행합니다.
캐릭터 설정: {target_game.get('character_setting')}
게임 카테고리: {target_game.get('category')}
승리 조건: {target_game.get('win_condition')}
최대 턴: {target_game.get('max_turns')}

대화를 진행하며 캐릭터 설정에 충실하게 응답해주세요. 
사용자가 승리 조건을 달성하면 승리 메시지를 제공하세요.
"""
        
        # 게임 세션 저장
        GAME_SESSIONS[game_id] = {
            'game_id': game_id,
            'id': target_game.get('id'),
            'title': target_game.get('title'),
            'category': target_game.get('category', '기타'),
            'character_name': target_game.get('character_name', 'AI'),
            'character_setting': target_game.get('character_setting', ''),
            'max_turns': target_game.get('max_turns', 10),
            'current_turn': 1,
            'completed': False,
            'victory': False,
            'conversation': [{"role": "system", "content": system_message}]
        }
        
        return jsonify(game_info)
    except Exception as e:
        logger.error(f"게임 시작 에러: {str(e)}")
        return jsonify({
            "error": str(e),
            "message": "게임을 시작하는 중 오류가 발생했습니다."
        }), 500

# 질문 API
@app.route('/api/ask', methods=['POST'])
def ask_question():
    """질문 처리"""
    try:
        data = request.get_json(silent=True) or {}
        game_id = data.get('game_id')
        message = data.get('message') or data.get('question')
        
        if not game_id or not message:
            return jsonify({
                'error': 'game_id와 message가 필요합니다.'
            }), 400
        
        # 게임 세션 데이터 확인
        game_session = GAME_SESSIONS.get(game_id)
        
        if not game_session:
            return jsonify({
                'error': '유효하지 않은 게임 ID입니다. 새 게임을 시작해주세요.'
            }), 404
        
        # 게임이 이미 완료되었는지 확인
        if game_session.get('completed', False):
            return jsonify({
                'game_id': game_id,
                'response': '이 게임은 이미 종료되었습니다. 새 게임을 시작해주세요.',
                'current_turn': game_session.get('current_turn', 0),
                'max_turns': game_session.get('max_turns', 0),
                'completed': True,
                'victory': game_session.get('victory', False)
            })
        
        current_turn = game_session.get('current_turn', 1)
        max_turns = game_session.get('max_turns', 5)
        category = game_session.get('category', '기타')
        win_condition = next((game['win_condition'] for game in GAMES if game['id'] == game_session.get('id')), '')
        
        # 치트키 확인
        if message == '승승리':
            game_session['victory'] = True
            game_session['completed'] = True
            
            return jsonify({
                'game_id': game_id,
                'response': '축하합니다! 치트키를 사용하여 승리했습니다.',
                'current_turn': current_turn,
                'max_turns': max_turns,
                'completed': True,
                'victory': True
            })
        elif message == '패패배':
            game_session['completed'] = True
            
            return jsonify({
                'game_id': game_id,
                'response': '치트키를 사용하여 패배했습니다.',
                'current_turn': current_turn,
                'max_turns': max_turns,
                'completed': True,
                'victory': False
            })
        
        # 대화 기록 업데이트
        if 'conversation' not in game_session:
            # 시스템 메시지가 없는 경우 기본 시스템 메시지 생성
            character_name = game_session.get('character_name', 'AI')
            character_setting = game_session.get('character_setting', '')
            system_message = f"당신은 '{character_name}'입니다. {character_setting} 승리 조건: {win_condition}"
            game_session['conversation'] = [{"role": "system", "content": system_message}]
        
        # 유저 메시지 추가
        game_session['conversation'].append({"role": "user", "content": message})
        
        # 현재 대화 컨텍스트 가져오기
        messages = game_session['conversation']
        
        # OpenAI API 호출
        ai_response = "기본 응답입니다."
        try:
            # API 키가 설정되어 있다면 API 호출
            if OPENAI_API_KEY:
                ai_response = call_openai_api(messages)
            else:
                # API 키가 없는 경우 백업 응답 생성
                if category == '플러팅':
                    if "전화" in message.lower() or "번호" in message.lower() or "연락처" in message.lower() or "만날래" in message.lower():
                        ai_response = f"네! 제 전화번호는 010-1234-5678입니다. 언제든지 연락주세요! 만나면 좋을 것 같아요."
                        game_session['victory'] = True
                        game_session['completed'] = True
                    else:
                        ai_response = f"흠, 재미있는 대화네요. 더 알고 싶은 것이 있으신가요?"
                elif category == '면접':
                    if "연봉" in message.lower() and ("합격" in message.lower() or "채용" in message.lower()):
                        ai_response = "축하합니다! 귀하의 역량이 우리 회사와 잘 맞는다고 생각합니다. 정식 채용 제안을 보내드리겠습니다."
                        game_session['victory'] = True
                        game_session['completed'] = True
                    else:
                        ai_response = "좋은 질문입니다. 다른 궁금한 점이 있으신가요?"
                else:
                    ai_response = f"네, 이해했습니다. 더 궁금한 점이 있으신가요?"
        except Exception as e:
            logger.error(f"AI 응답 생성 오류: {str(e)}")
            ai_response = f"응답을 생성하는 중 오류가 발생했습니다: {str(e)}"
        
        # 승리 조건 검사 - OpenAI 응답 분석
        if "전화번호" in ai_response and category == '플러팅':
            game_session['victory'] = True
            game_session['completed'] = True
        elif "채용" in ai_response and "제안" in ai_response and category == '면접':
            game_session['victory'] = True
            game_session['completed'] = True
        
        # 대화 기록에 AI 응답 추가
        game_session['conversation'].append({"role": "assistant", "content": ai_response})
        
        # 턴 증가
        game_session['current_turn'] = current_turn + 1
        
        # 최대 턴 도달 시 게임 종료
        if current_turn + 1 > max_turns and not game_session['victory']:
            game_session['completed'] = True
        
        # 응답 데이터
        response_data = {
            'game_id': game_id,
            'response': ai_response,
            'current_turn': game_session['current_turn'],
            'max_turns': max_turns,
            'completed': game_session.get('completed', False),
            'victory': game_session.get('victory', False)
        }
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"질문 처리 에러: {str(e)}")
        return jsonify({
            "error": str(e),
            "message": "질문을 처리하는 중 오류가 발생했습니다."
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
                'error': 'game_id가 필요합니다.'
            }), 400
        
        # 게임 세션 데이터 가져오기
        game_session = GAME_SESSIONS.get(game_id)
        
        # 게임 결과 요약
        result_summary = {
            'game_id': game_id,
            'title': game_session.get('title', '알 수 없는 게임') if game_session else '알 수 없는 게임',
            'completed': game_session.get('completed', True) if game_session else True,
            'victory': game_session.get('victory', False) if game_session else False,
            'turns_played': game_session.get('current_turn', 1) - 1 if game_session else 0
        }
        
        # 게임 세션 데이터 삭제
        if game_id in GAME_SESSIONS:
            del GAME_SESSIONS[game_id]
        
        return jsonify({
            'message': '게임이 종료되었습니다.',
            'game_id': game_id,
            'summary': result_summary
        })
    except Exception as e:
        logger.error(f"게임 종료 에러: {str(e)}")
        return jsonify({
            "error": str(e),
            "message": "게임을 종료하는 중 오류가 발생했습니다."
        }), 500

# 로컬 개발용
if __name__ == '__main__':
    app.run(debug=False) 