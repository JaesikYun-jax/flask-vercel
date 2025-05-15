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
OPENAI_AVAILABLE = bool(OPENAI_API_KEY)

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
            "environment_keys": [k for k in os.environ.keys() 
                          if not k.startswith('AWS_') 
                          and not 'SECRET' in k.upper() 
                          and not 'KEY' in k.upper()],
            "active_game_sessions": len(GAME_SESSIONS),
            "games_available": len(GAMES),
            "server_time": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "vercel_deployment_id": os.environ.get('VERCEL_DEPLOYMENT_ID', 'local'),
            "openai_api_configured": OPENAI_AVAILABLE
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
        
        # 대화 기록 업데이트
        if 'conversation' not in game_session:
            game_session['conversation'] = []
        
        game_session['conversation'].append({"role": "user", "content": message})
        
        # OpenAI API 사용 가능성 확인
        if OPENAI_AVAILABLE:
            # OPENAI API 사용 가능 시 나중에 외부 API 연동
            ai_response = f"OpenAI API 통합 준비됨 - 현재는 카테고리({category})별 기본 응답 제공: {message}"
        else:
            # 카테고리별 응답 생성
            if category == '플러팅':
                if "전화" in message.lower() or "번호" in message.lower() or "연락처" in message.lower() or "만날래" in message.lower():
                    ai_response = f"네! 제 전화번호는 010-1234-5678입니다. 언제든지 연락주세요! 만나면 좋을 것 같아요."
                    game_session['victory'] = True
                    game_session['completed'] = True
                elif "이름" in message.lower() or "누구" in message.lower():
                    ai_response = f"제 이름은 {character_name}입니다. 만나서 반가워요!"
                elif "직업" in message.lower() or "일" in message.lower() or "뭐하" in message.lower():
                    ai_response = "저는 디자인 회사에서 UX 디자이너로 일하고 있어요. 사용자 경험 디자인에 관심이 많답니다."
                elif "취미" in message.lower() or "관심" in message.lower():
                    ai_response = "저는 여행과 사진 찍기를 좋아해요. 요즘은 베이킹에도 관심이 생겼어요. 당신은 어떤 취미가 있나요?"
                elif "나이" in message.lower() or "몇 살" in message.lower():
                    ai_response = "저는 28살이에요. 나이보다 젊게 보인다는 말을 자주 들어요. 당신은요?"
                else:
                    ai_response = f"흠, 재미있는 대화네요. 더 알고 싶은 것이 있으신가요?"
            elif category == '면접':
                if "경력" in message.lower() or "경험" in message.lower():
                    ai_response = "저희 회사에서는 이 분야에서 최소 3년 이상의 경험을 가진 분을 찾고 있습니다. 귀하의 경험을 더 자세히 말씀해주시겠어요?"
                elif "강점" in message.lower() or "장점" in message.lower():
                    ai_response = "자신의 강점과 그것이 우리 회사에 어떻게 도움이 될 수 있는지 구체적인 사례와 함께 설명해주시면 좋겠습니다."
                elif "약점" in message.lower() or "단점" in message.lower():
                    ai_response = "자신의 약점을 인식하고 개선하려는 노력이 중요합니다. 어떤 부분을 개선하고 계신가요?"
                elif "연봉" in message.lower() or "급여" in message.lower() or "보상" in message.lower():
                    ai_response = "연봉 범위는 경험과 기술에 따라 다릅니다. 귀하의 기대치는 어느 정도인가요?"
                    if "합격" in message.lower() or "채용" in message.lower() or "제안" in message.lower():
                        ai_response = "축하합니다! 귀하의 역량이 우리 회사와 잘 맞는다고 생각합니다. 정식 채용 제안을 보내드리겠습니다."
                        game_session['victory'] = True
                        game_session['completed'] = True
                else:
                    ai_response = "좋은 질문입니다. 저희 회사에 관심을 가져주셔서 감사합니다. 다른 궁금한 점이 있으신가요?"
            else:
                # 기본 응답
                if "안녕" in message.lower() or "반갑" in message.lower():
                    ai_response = f"안녕하세요! 저는 {character_name}입니다. 무엇을 도와드릴까요?"
                elif "고마워" in message.lower() or "감사" in message.lower():
                    ai_response = "천만에요! 더 필요한 것이 있으시면 언제든지 말씀해주세요."
                elif "도움" in message.lower() or "어떻게" in message.lower():
                    ai_response = "어떤 도움이 필요하신가요? 최대한 자세히 알려주시면 더 잘 도와드릴 수 있어요."
                else:
                    ai_response = f"네, 이해했습니다. 더 궁금한 점이 있으신가요?"
        
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