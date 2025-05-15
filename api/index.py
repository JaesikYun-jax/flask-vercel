"""
AI 추측 게임 API 서버 - 최소 버전
"""
import os
import json
import time
import random
from flask import Flask, jsonify, request

# Flask 앱 초기화
app = Flask(__name__)

# 게임 세션 저장소
GAME_SESSIONS = {}

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

# 게임 목록 API
@app.route('/api/games')
def list_games():
    """게임 목록 반환"""
    games = [
        {
            "id": 1,
            "title": "플러팅 고수! 전화번호 따기",
            "category": "플러팅",
            "character_name": "윤지혜", 
            "max_turns": 5,
            "win_condition": "상대방의 전화번호를 얻어낸다",
            "difficulty": "보통"
        },
        {
            "id": 2,
            "title": "파티에서 번호 교환하기",
            "category": "플러팅",
            "character_name": "김민준",
            "max_turns": 4,
            "win_condition": "상대방과 번호를 교환한다",
            "difficulty": "쉬움"
        }
    ]
    return jsonify({
        "success": True,
        "data": games
    })

# 게임 시작 API
@app.route('/api/start', methods=['POST'])
def start_game():
    """게임 시작"""
    try:
        data = request.get_json(silent=True) or {}
        
        # 선택된 게임 ID (선택 사항)
        selected_game_id = data.get('item_id') or data.get('game_id')
        
        # 테스트 모드 확인
        is_test = data.get('test') or (request.args.get('test') == 'true')
        
        # 게임 목록 가져오기
        games = [
            {
                "id": 1,
                "title": "플러팅 고수! 전화번호 따기",
                "category": "플러팅",
                "character_name": "윤지혜", 
                "character_setting": "당신은 카페에서 우연히 마주친 매력적인 사람입니다. 친절하지만 쉽게 개인정보를 알려주지 않는 성격입니다.",
                "max_turns": 5,
                "win_condition": "상대방의 전화번호를 얻어낸다",
                "lose_condition": "턴 제한을 초과하거나 상대방이 대화를 거부한다",
                "difficulty": "보통"
            },
            {
                "id": 2,
                "title": "파티에서 번호 교환하기",
                "category": "플러팅",
                "character_name": "김민준",
                "character_setting": "당신은 친구의 파티에서 만난 사람입니다. 사교적이지만 많은 사람들에게 관심을 받고 있어 쉽게 번호를 주지 않습니다.",
                "max_turns": 4,
                "win_condition": "상대방과 번호를 교환한다",
                "lose_condition": "턴 제한을 초과하거나 상대방이 관심을 잃는다",
                "difficulty": "쉬움"
            }
        ]
        
        # 게임 선택
        if not selected_game_id:
            # 게임 ID가 제공되지 않은 경우 랜덤 선택
            target_game = random.choice(games)
        else:
            # 선택된 ID로 게임 찾기
            try:
                if isinstance(selected_game_id, str) and selected_game_id.isdigit():
                    selected_game_id = int(selected_game_id)
                
                target_game = next((game for game in games if game['id'] == selected_game_id), None)
                
                if not target_game:
                    target_game = random.choice(games)
            except:
                target_game = random.choice(games)
        
        # 게임 ID 생성
        if is_test:
            # 테스트 모드에서는 항상 일관된 게임 ID 반환
            game_id = f"test_game_{target_game['id']}"
        else:
            # 일반 모드에서는 랜덤 ID 생성
            game_id = f"game_{random.randint(10000, 99999)}"
        
        # 환영 메시지 생성
        welcome_message = f"안녕하세요! '{target_game['title']}' 상황에 오신 것을 환영합니다. 이 상황에서 여러분은 {target_game['max_turns']}턴 안에 '{target_game['win_condition']}'을(를) 달성해야 합니다. 대화를 통해 목표를 이루어보세요!"
        
        # 게임 정보 생성
        game_info = {
            "game_id": game_id,
            "id": target_game.get('id'),
            "title": target_game.get('title'),
            "category": target_game.get('category'),
            "character_name": target_game.get('character_name'),
            "character_setting": target_game.get('character_setting', ''),
            "max_turns": target_game.get('max_turns'),
            "current_turn": 1,
            "win_condition": target_game.get('win_condition'),
            "lose_condition": target_game.get('lose_condition', ''),
            "difficulty": target_game.get('difficulty'),
            "completed": False,
            "victory": False,
            "creation_time": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "welcome_message": welcome_message
        }
        
        # 게임 세션 저장
        GAME_SESSIONS[game_id] = game_info
        
        # 클라이언트에 반환할 정보
        response_data = {
            "game_id": game_id,
            "title": target_game.get('title'),
            "category": target_game.get('category'),
            "character_name": target_game.get('character_name'),
            "max_turns": target_game.get('max_turns'),
            "current_turn": 1,
            "win_condition": target_game.get('win_condition'),
            "welcome_message": welcome_message
        }
        
        return jsonify({
            "success": True,
            "data": response_data
        })
        
    except Exception as e:
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
        message = data.get('message') or data.get('question')
        
        # 디버그 정보 기록
        is_test = game_id and 'test' in game_id.lower()
        
        if not game_id or not message:
            return jsonify({
                'error': 'game_id와 message가 필요합니다.'
            }), 400
        
        # 게임 세션 데이터 확인
        game_session = GAME_SESSIONS.get(game_id)
        
        # 테스트 모드 - 유효한 game_id가 없어도 응답
        if not game_session and is_test:
            # 테스트용 게임 세션 생성
            game_session = {
                "game_id": game_id,
                "id": 1,
                "title": "플러팅 고수! 전화번호 따기",
                "category": "플러팅",
                "character_name": "윤지혜",
                "character_setting": "당신은 카페에서 우연히 마주친 매력적인 사람입니다. 친절하지만 쉽게 개인정보를 알려주지 않는 성격입니다.",
                "max_turns": 5,
                "current_turn": 1,
                "win_condition": "상대방의 전화번호를 얻어낸다",
                "lose_condition": "턴 제한을 초과하거나 상대방이 대화를 거부한다",
                "difficulty": "보통",
                "completed": False,
                "victory": False
            }
            # 테스트용 세션 저장
            GAME_SESSIONS[game_id] = game_session
        
        # 일반 모드 - 유효하지 않은 게임 ID는 오류 반환
        if not game_session:
            return jsonify({
                'error': '유효하지 않은 게임 ID입니다. 새 게임을 시작해주세요.',
                'code': 'INVALID_GAME_ID'
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
        character_name = game_session.get('character_name', 'AI')
        category = game_session.get('category', '기타')
        
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
        
        # AI 응답 생성 (간단한 규칙 기반 응답)
        ai_response = ""
        victory = False
        
        # 카테고리별 응답 생성
        if category == '플러팅':
            if "전화" in message.lower() or "번호" in message.lower() or "연락처" in message.lower() or "만날래" in message.lower():
                ai_response = f"네! 제 전화번호는 010-1234-5678입니다. 언제든지 연락주세요! 만나면 좋을 것 같아요."
                victory = True
            else:
                responses = [
                    f"안녕하세요! 저는 {character_name}입니다. 어떻게 도와드릴까요?",
                    "그렇군요. 더 자세히 이야기해 주실래요?",
                    "재미있는 이야기네요. 어떤 일을 하시나요?",
                    "방금 말씀하신 내용이 정말 흥미롭네요. 계속 말씀해주세요.",
                    "오늘 날씨가 정말 좋네요, 그렇지 않나요?"
                ]
                ai_response = random.choice(responses)
        else:
            responses = [
                f"안녕하세요! 저는 {character_name}입니다. 어떻게 도와드릴까요?",
                "그렇군요. 더 자세히 이야기해 주실래요?",
                "흥미로운 질문이네요. 다른 것도 궁금하신 점이 있으신가요?",
                "네, 이해했습니다. 더 궁금한 점이 있으신가요?"
            ]
            ai_response = random.choice(responses)
        
        # 게임 상태 업데이트
        game_session['current_turn'] = current_turn + 1
        
        if victory:
            game_session['victory'] = True
            game_session['completed'] = True
        elif current_turn + 1 > max_turns:
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
        
        # 테스트 모드 확인
        is_test = game_id and 'test' in game_id.lower()
        
        if not game_id:
            return jsonify({
                'error': 'game_id가 필요합니다.'
            }), 400
        
        # 게임 세션 데이터 가져오기
        game_session = GAME_SESSIONS.get(game_id)
        
        # 테스트 모드에서는 게임 세션이 없어도 응답
        if not game_session and is_test:
            game_session = {
                "game_id": game_id,
                "title": "테스트 게임",
                "completed": True,
                "victory": False,
                "current_turn": 1
            }
        
        # 게임 결과 요약
        result_summary = {
            'game_id': game_id,
            'title': game_session.get('title', '알 수 없는 게임') if game_session else '알 수 없는 게임',
            'completed': game_session.get('completed', True) if game_session else True,
            'victory': game_session.get('victory', False) if game_session else False,
            'turns_played': game_session.get('current_turn', 1) - 1 if game_session else 0
        }
        
        # 게임 세션 데이터 삭제 (테스트 모드가 아닌 경우에만)
        if game_id in GAME_SESSIONS and not is_test:
            del GAME_SESSIONS[game_id]
        
        return jsonify({
            'message': '게임이 종료되었습니다.',
            'game_id': game_id,
            'summary': result_summary
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "게임을 종료하는 중 오류가 발생했습니다."
        }), 500

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

# 로컬 개발용
if __name__ == '__main__':
    app.run(debug=False) 