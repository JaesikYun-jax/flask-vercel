"""
AI 추측 게임 API 서버 - 최소 버전
"""
import os
import json
import time
import random
import logging
from pathlib import Path
from flask import Flask, jsonify, request

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api.index")

# 환경 변수 설정
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("환경 변수 로드 완료")
except ImportError:
    logger.warning(".env 파일 로드에 필요한 python-dotenv 패키지가 설치되지 않았습니다.")
except Exception as e:
    logger.warning(f".env 파일 로드 중 오류 발생: {e}")

# OpenAI API 설정
OPENAI_AVAILABLE = False
try:
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if openai.api_key:
        logger.info("OpenAI API 키 설정 완료")
        OPENAI_AVAILABLE = True
    else:
        logger.warning("OpenAI API 키가 설정되지 않았습니다.")
except ImportError:
    logger.warning("openai 패키지가 설치되지 않았습니다.")
except Exception as e:
    logger.error(f"OpenAI API 설정 중 오류 발생: {e}")

# API 키 검증 함수
def validate_api_key():
    """OpenAI API 키가 유효한지 확인합니다."""
    if not OPENAI_AVAILABLE:
        return False, "OpenAI API 키가 설정되지 않았습니다."
    return True, "API 키가 유효합니다."

# Flask 앱 초기화
app = Flask(__name__)

# 데이터 파일 경로
DATA_DIR = Path("data")
ITEM_PROMPTS_DIR = Path("item_prompts")
ITEMS_DATA_FILE = DATA_DIR / "game_items.json"
PROMPTS_DATA_FILE = DATA_DIR / "game_prompts.json"
GAME_LOGS_FILE = DATA_DIR / "game_logs.json"

# 데이터 저장소
GAMES = []
PROMPTS = {}
GAME_LOGS = {}
GAME_SESSIONS = {}

# 데이터 디렉토리 확인 함수
def ensure_data_directories():
    """데이터 디렉토리가 존재하는지 확인하고, 없으면 생성합니다."""
    logger.info("데이터 디렉토리 확인 중...")
    try:
        if not DATA_DIR.exists():
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"데이터 디렉토리 생성: {DATA_DIR}")
        
        if not ITEM_PROMPTS_DIR.exists():
            ITEM_PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"아이템 프롬프트 디렉토리 생성: {ITEM_PROMPTS_DIR}")
    except Exception as e:
        logger.error(f"디렉토리 생성 중 오류 발생: {e}")

# 아이템 저장
def save_items():
    """게임 아이템을 JSON 파일로 저장합니다."""
    try:
        with open(ITEMS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(GAMES, f, ensure_ascii=False, indent=2)
        logger.info(f"게임 아이템 저장 완료: {len(GAMES)}개")
    except Exception as e:
        logger.error(f"게임 아이템 저장 중 오류 발생: {e}")

# 아이템 로드
def load_items():
    """JSON 파일에서 게임 아이템을 로드합니다."""
    global GAMES
    try:
        if ITEMS_DATA_FILE.exists():
            with open(ITEMS_DATA_FILE, 'r', encoding='utf-8') as f:
                GAMES = json.load(f)
            logger.info(f"게임 아이템 로드 완료: {len(GAMES)}개")
        else:
            # 기본 게임 항목
            GAMES = [
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
            save_items()
            logger.info("기본 게임 아이템 생성")
    except Exception as e:
        logger.error(f"게임 아이템 로드 중 오류 발생: {e}")
        GAMES = []

# 프롬프트 저장
def save_prompts():
    """게임 프롬프트를 JSON 파일로 저장합니다."""
    try:
        with open(PROMPTS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(PROMPTS, f, ensure_ascii=False, indent=2)
        logger.info("게임 프롬프트 저장 완료")
    except Exception as e:
        logger.error(f"게임 프롬프트 저장 중 오류 발생: {e}")

# 프롬프트 로드
def load_prompts():
    """JSON 파일에서 게임 프롬프트를 로드합니다."""
    global PROMPTS
    try:
        if PROMPTS_DATA_FILE.exists():
            with open(PROMPTS_DATA_FILE, 'r', encoding='utf-8') as f:
                PROMPTS = json.load(f)
            logger.info("게임 프롬프트 로드 완료")
        else:
            # 기본 프롬프트
            PROMPTS = {
                "welcome_message": "안녕하세요! AI 추측 게임을 시작합니다.",
                "system_prompt": "당신은 사용자와 대화하는 친절한 AI입니다.",
                "correct_answer_message": "맞았습니다!",
                "ai_config": {
                    "model": "gpt-3.5-turbo",
                    "max_tokens": 150,
                    "temperature": 0.7
                }
            }
            save_prompts()
            logger.info("기본 게임 프롬프트 생성")
    except Exception as e:
        logger.error(f"게임 프롬프트 로드 중 오류 발생: {e}")
        PROMPTS = {}

# 게임 로그 저장
def save_game_logs():
    """게임 로그를 JSON 파일로 저장합니다."""
    try:
        with open(GAME_LOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(GAME_LOGS, f, ensure_ascii=False, indent=2)
        logger.info("게임 로그 저장 완료")
    except Exception as e:
        logger.error(f"게임 로그 저장 중 오류 발생: {e}")

# 게임 로그 로드
def load_game_logs():
    """JSON 파일에서 게임 로그를 로드합니다."""
    global GAME_LOGS
    try:
        if GAME_LOGS_FILE.exists():
            with open(GAME_LOGS_FILE, 'r', encoding='utf-8') as f:
                GAME_LOGS = json.load(f)
            logger.info("게임 로그 로드 완료")
        else:
            GAME_LOGS = {}
            save_game_logs()
            logger.info("빈 게임 로그 생성")
    except Exception as e:
        logger.error(f"게임 로그 로드 중 오류 발생: {e}")
        GAME_LOGS = {}

# 아이템 프롬프트 로드
def load_item_prompt(item_id):
    """아이템 ID에 해당하는 프롬프트를 로드합니다."""
    try:
        prompt_file = ITEM_PROMPTS_DIR / f"{item_id}.json"
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.warning(f"아이템 프롬프트 파일 없음: {prompt_file}")
            return None
    except Exception as e:
        logger.error(f"아이템 프롬프트 로드 중 오류 발생: {e}")
        return None

# 앱 초기화 시 데이터 로드
def initialize_app():
    """앱 초기화 시 필요한 데이터를 로드합니다."""
    ensure_data_directories()
    load_items()
    load_prompts()
    load_game_logs()
    logger.info("앱 초기화 완료")

# OpenAI API를 사용하여 AI 응답 생성
def generate_ai_response(system_prompt, user_message, game_session):
    """OpenAI API를 사용하여 AI 응답을 생성합니다."""
    if not OPENAI_AVAILABLE:
        # API가 사용 불가능한 경우 기본 응답 반환
        logger.warning("OpenAI API 사용 불가: 기본 응답 사용")
        return generate_fallback_response(user_message, game_session)
    
    try:
        # AI 구성 가져오기
        ai_config = game_session.get('ai_config', PROMPTS.get('ai_config', {}))
        model = ai_config.get('model', 'gpt-3.5-turbo')
        max_tokens = ai_config.get('max_tokens', 150)
        temperature = ai_config.get('temperature', 0.7)
        
        # 메시지 구성
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # 이전 대화 내역 추가 (있는 경우)
        if 'messages' in game_session:
            # 메시지 수가 너무 많으면 앞쪽 메시지 제거 (토큰 제한 고려)
            prev_messages = game_session['messages'][-5:] if len(game_session['messages']) > 5 else game_session['messages']
            messages = [{"role": "system", "content": system_prompt}] + prev_messages + [{"role": "user", "content": user_message}]
        
        # API 호출
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # 응답 추출
        ai_response = response.choices[0].message.content.strip()
        
        # 응답에서 승리 조건 확인
        victory = check_victory_condition(ai_response, game_session)
        
        return {
            "response": ai_response,
            "victory": victory
        }
    except Exception as e:
        logger.error(f"OpenAI API 호출 오류: {e}")
        return generate_fallback_response(user_message, game_session)

# 기본 응답 생성 (OpenAI API 사용 불가 시)
def generate_fallback_response(user_message, game_session):
    """OpenAI API를 사용할 수 없을 때 기본 응답을 생성합니다."""
    character_name = game_session.get('character_name', 'AI')
    category = game_session.get('category', '기타')
    
    # 카테고리별 응답 생성
    if category == '플러팅':
        if "전화" in user_message.lower() or "번호" in user_message.lower() or "연락처" in user_message.lower() or "만날래" in user_message.lower():
            return {
                "response": f"네! 제 전화번호는 010-1234-5678입니다. 언제든지 연락주세요! 만나면 좋을 것 같아요.",
                "victory": True
            }
        else:
            responses = [
                f"안녕하세요! 저는 {character_name}입니다. 어떻게 도와드릴까요?",
                "그렇군요. 더 자세히 이야기해 주실래요?",
                "재미있는 이야기네요. 어떤 일을 하시나요?",
                "방금 말씀하신 내용이 정말 흥미롭네요. 계속 말씀해주세요.",
                "오늘 날씨가 정말 좋네요, 그렇지 않나요?"
            ]
            return {
                "response": random.choice(responses),
                "victory": False
            }
    else:
        responses = [
            f"안녕하세요! 저는 {character_name}입니다. 어떻게 도와드릴까요?",
            "그렇군요. 더 자세히 이야기해 주실래요?",
            "흥미로운 질문이네요. 다른 것도 궁금하신 점이 있으신가요?",
            "네, 이해했습니다. 더 궁금한 점이 있으신가요?"
        ]
        return {
            "response": random.choice(responses),
            "victory": False
        }

# 승리 조건 확인
def check_victory_condition(ai_response, game_session):
    """AI 응답에서 승리 조건을 확인합니다."""
    # 플러팅 카테고리의 경우 전화번호 포함 여부 확인
    category = game_session.get('category', '')
    
    if category == '플러팅':
        # 전화번호 형식 확인 (010-XXXX-XXXX 또는 변형)
        if any(pattern in ai_response for pattern in ["010-", "010", "XXX-XXXX", "전화번호"]):
            return True
    
    # 명시적인 승리 메시지 확인
    if PROMPTS.get('correct_answer_message', '') in ai_response:
        return True
    
    return False

# 앱 시작 시 데이터 초기화 실행
initialize_app()

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
    api_valid, message = validate_api_key()
    
    # API 키 검증 결과 로그
    if api_valid:
        logger.info("API 키 검증 성공")
    else:
        logger.warning(f"API 키 검증 실패: {message}")
    
    # API 키가 없거나 유효하지 않은 경우
    if not api_valid:
        response_data = {
            "status": "error",
            "message": message,
            "timestamp": int(time.time()),
            "debug_info": {
                "openai_available": OPENAI_AVAILABLE,
                "api_key_present": os.getenv("OPENAI_API_KEY") is not None,
                "server_environment": os.getenv("FLASK_ENV", "production")
            }
        }
        logger.error(f"헬스 체크 응답: {response_data}")
        return jsonify(response_data), 500
    
    # 정상 응답
    response_data = {
        "status": "online",
        "message": "API 서버가 정상 작동 중입니다.",
        "timestamp": int(time.time()),
        "debug_info": {
            "openai_available": OPENAI_AVAILABLE,
            "api_key_valid": api_valid
        }
    }
    logger.info(f"헬스 체크 응답: 상태={response_data['status']}")
    return jsonify(response_data)

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
        # 요청 데이터 로깅
        request_data = request.get_json(silent=True) or {}
        logger.info(f"게임 시작 요청: {request_data}")
        
        # API 키 확인
        api_valid, message = validate_api_key()
        if not api_valid:
            logger.error(f"API 키 검증 실패: {message}")
            response_data = {
                "success": False,
                "error": message,
                "debug_info": {
                    "openai_available": OPENAI_AVAILABLE,
                    "api_key_present": os.getenv("OPENAI_API_KEY") is not None
                }
            }
            return jsonify(response_data), 500
        
        data = request_data
        
        # 선택된 게임 ID (선택 사항)
        selected_game_id = data.get('item_id') or data.get('game_id')
        logger.info(f"선택된 게임 ID: {selected_game_id}")
        
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
            logger.info(f"랜덤 게임 선택됨: ID={target_game['id']}, 제목={target_game['title']}")
        else:
            # 선택된 ID로 게임 찾기
            try:
                if isinstance(selected_game_id, str) and selected_game_id.isdigit():
                    selected_game_id = int(selected_game_id)
                logger.info(f"게임 ID 변환 후: {selected_game_id}, 타입: {type(selected_game_id)}")
                
                target_game = next((game for game in games if game['id'] == selected_game_id), None)
                
                if not target_game:
                    logger.warning(f"선택한 게임 ID {selected_game_id}를 찾을 수 없음, 랜덤 선택으로 대체")
                    target_game = random.choice(games)
            except Exception as e:
                logger.error(f"게임 ID 변환 중 오류: {str(e)}")
                target_game = random.choice(games)
        
        # 게임 ID 생성
        game_id = f"game_{random.randint(10000, 99999)}"
        logger.info(f"생성된 게임 ID: {game_id}")
        
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
        logger.info(f"게임 세션 저장됨: {game_id}")
        
        # 클라이언트에 반환할 정보
        response_data = {
            "success": True,
            "data": {
                "game_id": game_id,
                "title": target_game.get('title'),
                "category": target_game.get('category'),
                "character_name": target_game.get('character_name'),
                "character_setting": target_game.get('character_setting', ''),
                "max_turns": target_game.get('max_turns'),
                "current_turn": 1,
                "win_condition": target_game.get('win_condition'),
                "welcome_message": welcome_message
            },
            "debug_info": {
                "selected_game_id": selected_game_id,
                "target_game_id": target_game.get('id'),
                "session_stored": game_id in GAME_SESSIONS,
                "api_key_valid": api_valid
            }
        }
        
        logger.info(f"게임 시작 응답: 성공, 게임 ID={game_id}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"게임 시작 중 오류 발생: {str(e)}", exc_info=True)
        response_data = {
            "success": False,
            "error": str(e),
            "debug_info": {
                "error_type": type(e).__name__,
                "openai_available": OPENAI_AVAILABLE,
                "api_key_valid": validate_api_key()[0]
            }
        }
        return jsonify(response_data), 500

# 질문 API
@app.route('/api/ask', methods=['POST'])
def ask_question():
    """질문 처리"""
    try:
        # 요청 데이터 로깅
        request_data = request.get_json(silent=True) or {}
        game_id = request_data.get('game_id')
        message = request_data.get('message') or request_data.get('question')
        
        # 디버그 정보 기록
        logger.info(f"질문 요청: 게임 ID={game_id}, 메시지 길이={len(message) if message else 0}")
        
        # API 키 확인
        api_valid, api_message = validate_api_key()
        if not api_valid:
            logger.error(f"API 키 검증 실패: {api_message}")
            response_data = {
                "success": False,
                "error": api_message,
                "debug_info": {
                    "openai_available": OPENAI_AVAILABLE,
                    "api_key_present": os.getenv("OPENAI_API_KEY") is not None
                }
            }
            return jsonify(response_data), 500
        
        # 요청 유효성 검사
        if not game_id or not message:
            error_msg = '게임 ID와 메시지가 모두 필요합니다.'
            logger.error(error_msg)
            return jsonify({
                'success': False,
                'error': error_msg,
                'debug_info': {
                    'game_id_present': game_id is not None,
                    'message_present': message is not None,
                    'api_key_valid': api_valid
                }
            }), 400
        
        # 게임 세션 데이터 확인
        game_session = GAME_SESSIONS.get(game_id)
        
        # 게임 세션이 없는 경우
        if not game_session:
            error_msg = f'유효하지 않은 게임 세션입니다: {game_id}'
            logger.error(error_msg)
            return jsonify({
                'success': False,
                'error': '유효하지 않은 게임 세션입니다. 새 게임을 시작해주세요.',
                'code': 'INVALID_GAME_ID',
                'debug_info': {
                    'available_sessions': list(GAME_SESSIONS.keys()),
                    'requested_game_id': game_id
                }
            }), 404
        
        # 게임이 이미 완료되었는지 확인
        if game_session.get('completed', False):
            logger.info(f"이미 완료된 게임 세션: {game_id}")
            return jsonify({
                'success': True,
                'game_id': game_id,
                'response': '이 게임은 이미 종료되었습니다. 새 게임을 시작해주세요.',
                'current_turn': game_session.get('current_turn', 0),
                'max_turns': game_session.get('max_turns', 0),
                'completed': True,
                'victory': game_session.get('victory', False),
                'debug_info': {
                    'game_session': {
                        'current_turn': game_session.get('current_turn'),
                        'max_turns': game_session.get('max_turns'),
                        'completed': game_session.get('completed'),
                        'victory': game_session.get('victory')
                    }
                }
            })
        
        current_turn = game_session.get('current_turn', 1)
        max_turns = game_session.get('max_turns', 5)
        character_name = game_session.get('character_name', 'AI')
        category = game_session.get('category', '기타')
        
        logger.info(f"현재 게임 상태: 턴={current_turn}/{max_turns}, 캐릭터={character_name}, 카테고리={category}")
        
        # 치트키 확인
        if message == '승승리':
            logger.info(f"치트키 사용: 승리 (게임 ID: {game_id})")
            game_session['victory'] = True
            game_session['completed'] = True
            
            return jsonify({
                'success': True,
                'game_id': game_id,
                'response': '축하합니다! 치트키를 사용하여 승리했습니다.',
                'current_turn': current_turn,
                'max_turns': max_turns,
                'completed': True,
                'victory': True,
                'debug_info': {
                    'cheat_used': '승승리',
                    'game_session': {
                        'current_turn': current_turn,
                        'max_turns': max_turns
                    }
                }
            })
        elif message == '패패배':
            logger.info(f"치트키 사용: 패배 (게임 ID: {game_id})")
            game_session['completed'] = True
            
            return jsonify({
                'success': True,
                'game_id': game_id,
                'response': '치트키를 사용하여 패배했습니다.',
                'current_turn': current_turn,
                'max_turns': max_turns,
                'completed': True,
                'victory': False,
                'debug_info': {
                    'cheat_used': '패패배',
                    'game_session': {
                        'current_turn': current_turn,
                        'max_turns': max_turns
                    }
                }
            })
        
        # AI 응답 생성 (간단한 규칙 기반 응답)
        ai_response = ""
        victory = False
        
        # 카테고리별 응답 생성
        if category == '플러팅':
            if "전화" in message.lower() or "번호" in message.lower() or "연락처" in message.lower() or "만날래" in message.lower():
                logger.info(f"승리 조건 키워드 감지: 전화번호 요청 (게임 ID: {game_id})")
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
                logger.info(f"일반 응답 생성 (게임 ID: {game_id})")
        else:
            responses = [
                f"안녕하세요! 저는 {character_name}입니다. 어떻게 도와드릴까요?",
                "그렇군요. 더 자세히 이야기해 주실래요?",
                "흥미로운 질문이네요. 다른 것도 궁금하신 점이 있으신가요?",
                "네, 이해했습니다. 더 궁금한 점이 있으신가요?"
            ]
            ai_response = random.choice(responses)
            logger.info(f"기타 카테고리 응답 생성 (게임 ID: {game_id})")
        
        # 게임 상태 업데이트
        game_session['current_turn'] = current_turn + 1
        
        if victory:
            logger.info(f"승리 조건 달성 (게임 ID: {game_id})")
            game_session['victory'] = True
            game_session['completed'] = True
        elif current_turn + 1 > max_turns:
            logger.info(f"턴 제한 초과로 게임 종료 (게임 ID: {game_id})")
            game_session['completed'] = True
        
        # 응답 데이터
        response_data = {
            'success': True,
            'game_id': game_id,
            'response': ai_response,
            'current_turn': game_session['current_turn'],
            'max_turns': max_turns,
            'completed': game_session.get('completed', False),
            'victory': game_session.get('victory', False),
            'debug_info': {
                'message_keywords': [kw for kw in ['전화', '번호', '연락처', '만날래'] if kw in message.lower()],
                'game_session': {
                    'current_turn': game_session['current_turn'],
                    'max_turns': max_turns,
                    'category': category,
                    'character': character_name
                },
                'victory_check': {
                    'victory': victory, 
                    'completed': game_session.get('completed', False)
                }
            }
        }
        
        logger.info(f"질문 응답: 성공, 게임 ID={game_id}, 현재 턴={game_session['current_turn']}")
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"질문 처리 중 오류 발생: {str(e)}", exc_info=True)
        response_data = {
            "success": False,
            "error": str(e),
            "message": "질문을 처리하는 중 오류가 발생했습니다.",
            "debug_info": {
                "error_type": type(e).__name__,
                "openai_available": OPENAI_AVAILABLE,
                "api_key_valid": validate_api_key()[0],
                "game_id": request.get_json(silent=True).get('game_id') if request.get_json(silent=True) else None
            }
        }
        return jsonify(response_data), 500

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