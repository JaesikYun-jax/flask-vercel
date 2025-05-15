"""
AI 추측 게임 API 서버 - OpenAI 통합 버전
"""
import os
import json
import logging
import time
import random
import sys
import traceback
from flask import Flask, request, jsonify

# 로깅 강화
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # Vercel에서는 표준 출력으로 로그를 보냄
)
logger = logging.getLogger(__name__)

# 시작 로그
logger.info("=== API 서버 시작 중 ===")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current directory: {os.getcwd()}")

# Flask 앱 초기화
app = Flask(__name__)

# 게임 세션 데이터 저장소
GAME_SESSIONS = {}

# 데이터 파일 경로
ITEMS_DATA_FILE = "data/game_items.json"
PROMPTS_DATA_FILE = "data/game_prompts.json"
GAME_LOGS_FILE = "data/game_logs.json"

# 초기 빈 항목 리스트 선언
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
PROMPTS = {
    "system_prompt_template": "당신은 '상황 대처 게임'의 AI입니다.\n카테고리: {category}\n상황: {title}\n\n당신은 다음 상황에서 아래와 같은 캐릭터로 역할을 해야 합니다.\n{character_setting}\n\n규칙:\n1. 당신은 정해진 캐릭터로서 대화를 이어가야 합니다.\n2. 턴제 게임으로, 플레이어는 {max_turns}턴 안에 승리 조건을 달성해야 합니다.\n3. 현재 턴: {current_turn}/{max_turns}\n4. 승리 조건: {win_condition}\n5. 패배 조건: {lose_condition}\n6. 난이도: {difficulty}\n\n승리 조건이 충족되면 축하 메시지와 함께 게임이 종료됩니다.\n패배 조건이 충족되거나 턴을 모두 소진하면 게임이 종료됩니다.\n항상 현재 역할에 맞게 응답하세요.",
    "welcome_message": "안녕하세요! '{title}' 상황에 오신 것을 환영합니다. 이 상황에서 여러분은 {max_turns}턴 안에 '{win_condition}'을(를) 달성해야 합니다. 대화를 통해 목표를 이루어보세요!",
    "ai_config": {
        "model": "gpt-3.5-turbo",
        "max_tokens": 150,
        "temperature": 0.7
    }
}
GAME_LOGS = {}

# 관리자 인증 정보
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin1234')
ADMIN_SESSION_KEY = "admin_authenticated"

# 관리자 인증 필요 데코레이터
def admin_required(f):
    """관리자 인증 확인 데코레이터"""
    def decorated_function(*args, **kwargs):
        # Authorization 헤더 확인
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Basic '):
            import base64
            # Basic Authentication 디코딩
            credentials = base64.b64decode(auth_header[6:]).decode('utf-8')
            username, password = credentials.split(':')
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                return f(*args, **kwargs)
        
        return jsonify({
            "success": False,
            "error": "관리자 인증이 필요합니다."
        }), 401
    
    return decorated_function

# 관리자 로그인 API
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """관리자 로그인 처리"""
    try:
        data = request.get_json(silent=True) or {}
        
        username = data.get('username')
        password = data.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            return jsonify({
                "success": True,
                "message": "관리자 로그인 성공"
            })
        else:
            return jsonify({
                "success": False,
                "error": "아이디 또는 비밀번호가 일치하지 않습니다."
            }), 401
    except Exception as e:
        logger.error(f"관리자 로그인 에러: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 관리자 로그아웃 API
@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    """관리자 로그아웃 처리"""
    return jsonify({
        "success": True,
        "message": "로그아웃 되었습니다."
    })

# 게임 항목 관리 API (관리자 전용)
@app.route('/api/admin/items', methods=['GET'])
@admin_required
def get_items():
    """모든 게임 항목 조회"""
    try:
        return jsonify({
            "success": True,
            "data": GAMES
        })
    except Exception as e:
        logger.error(f"게임 항목 조회 에러: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 게임 항목 추가 API (관리자 전용)
@app.route('/api/admin/items', methods=['POST'])
@admin_required
def add_item():
    """새 게임 항목 추가"""
    try:
        data = request.get_json(silent=True) or {}
        
        # 필수 필드 확인
        required_fields = ['title', 'category', 'character_name', 'max_turns', 'win_condition']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"'{field}' 필드는 필수입니다."
                }), 400
        
        # 새 항목 ID 생성
        new_id = 1
        if GAMES:
            new_id = max([game.get('id', 0) for game in GAMES]) + 1
        
        # 새 항목 생성
        new_item = {
            "id": new_id,
            "title": data.get('title'),
            "category": data.get('category'),
            "character_name": data.get('character_name'),
            "character_setting": data.get('character_setting', ''),
            "max_turns": data.get('max_turns', 5),
            "win_condition": data.get('win_condition'),
            "lose_condition": data.get('lose_condition', '턴 제한을 초과하면 패배합니다.'),
            "difficulty": data.get('difficulty', '보통')
        }
        
        # 항목 추가
        GAMES.append(new_item)
        
        # 변경사항 저장
        save_items()
        
        return jsonify({
            "success": True,
            "data": new_item,
            "message": "새 게임 항목이 추가되었습니다."
        })
    except Exception as e:
        logger.error(f"게임 항목 추가 에러: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 게임 항목 수정 API (관리자 전용)
@app.route('/api/admin/items/<int:item_id>', methods=['PUT'])
@admin_required
def update_item(item_id):
    """게임 항목 수정"""
    try:
        data = request.get_json(silent=True) or {}
        
        # 항목 찾기
        item_index = -1
        for i, item in enumerate(GAMES):
            if item.get('id') == item_id:
                item_index = i
                break
        
        if item_index == -1:
            return jsonify({
                "success": False,
                "error": f"ID {item_id}인 게임 항목을 찾을 수 없습니다."
            }), 404
        
        # 항목 업데이트
        for key, value in data.items():
            if key != 'id':  # ID는 변경할 수 없음
                GAMES[item_index][key] = value
        
        # 변경사항 저장
        save_items()
        
        return jsonify({
            "success": True,
            "data": GAMES[item_index],
            "message": "게임 항목이 업데이트되었습니다."
        })
    except Exception as e:
        logger.error(f"게임 항목 수정 에러: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 게임 항목 삭제 API (관리자 전용)
@app.route('/api/admin/items/<int:item_id>', methods=['DELETE'])
@admin_required
def delete_item(item_id):
    """게임 항목 삭제"""
    try:
        # 항목 찾기
        item_index = -1
        for i, item in enumerate(GAMES):
            if item.get('id') == item_id:
                item_index = i
                break
        
        if item_index == -1:
            return jsonify({
                "success": False,
                "error": f"ID {item_id}인 게임 항목을 찾을 수 없습니다."
            }), 404
        
        # 항목 삭제
        deleted_item = GAMES.pop(item_index)
        
        # 변경사항 저장
        save_items()
        
        return jsonify({
            "success": True,
            "data": deleted_item,
            "message": "게임 항목이 삭제되었습니다."
        })
    except Exception as e:
        logger.error(f"게임 항목 삭제 에러: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 아이템별 프롬프트 조회 API (관리자 전용)
@app.route('/api/admin/items/<int:item_id>/prompt', methods=['GET'])
@admin_required
def get_item_prompt(item_id):
    """아이템별 프롬프트 조회"""
    try:
        # 항목 찾기
        item = None
        for game in GAMES:
            if game.get('id') == item_id:
                item = game
                break
        
        if not item:
            return jsonify({
                "success": False,
                "error": f"ID {item_id}인 게임 항목을 찾을 수 없습니다."
            }), 404
        
        # 아이템별 프롬프트 가져오기
        prompt_data = load_item_prompt(item_id)
        
        if not prompt_data:
            # 기본 프롬프트 구성
            prompt_data = {
                "system_prompt": PROMPTS.get('system_prompt_template', '').format(
                    title=item.get('title', '알 수 없는 게임'),
                    category=item.get('category', '기타'),
                    character_setting=item.get('character_setting', ''),
                    max_turns=item.get('max_turns', 5),
                    current_turn=1,
                    win_condition=item.get('win_condition', ''),
                    lose_condition=item.get('lose_condition', ''),
                    difficulty=item.get('difficulty', '보통')
                ),
                "welcome_message": PROMPTS.get('welcome_message', '').format(
                    title=item.get('title', '알 수 없는 게임'),
                    max_turns=item.get('max_turns', 5),
                    win_condition=item.get('win_condition', '')
                ),
                "ai_config": PROMPTS.get('ai_config', {})
            }
        
        return jsonify({
            "success": True,
            "data": prompt_data
        })
    except Exception as e:
        logger.error(f"아이템 프롬프트 조회 에러: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 아이템별 프롬프트 업데이트 API (관리자 전용)
@app.route('/api/admin/items/<int:item_id>/prompt', methods=['POST'])
@admin_required
def update_item_prompt(item_id):
    """아이템별 프롬프트 업데이트"""
    try:
        data = request.get_json(silent=True) or {}
        
        # 항목 찾기
        item = None
        for game in GAMES:
            if game.get('id') == item_id:
                item = game
                break
        
        if not item:
            return jsonify({
                "success": False,
                "error": f"ID {item_id}인 게임 항목을 찾을 수 없습니다."
            }), 404
        
        # 프롬프트 파일 경로
        prompt_file_name = f"{item_id}.json"
        prompt_file = os.path.join('item_prompts', prompt_file_name)
        file_path = get_file_path(prompt_file)
        
        # 디렉토리 확인 및 생성
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 프롬프트 파일 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 원본 위치에도 저장 (로컬 환경에서만)
        if not os.environ.get('VERCEL'):
            os.makedirs(os.path.dirname(prompt_file), exist_ok=True)
            with open(prompt_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            "success": True,
            "message": "아이템 프롬프트가 업데이트되었습니다."
        })
    except Exception as e:
        logger.error(f"아이템 프롬프트 업데이트 에러: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 글로벌 프롬프트 설정 가져오기 API (관리자 전용)
@app.route('/api/admin/prompts', methods=['GET'])
@admin_required
def get_prompts():
    """글로벌 프롬프트 설정 가져오기"""
    try:
        return jsonify({
            "success": True,
            "data": PROMPTS
        })
    except Exception as e:
        logger.error(f"프롬프트 설정 조회 에러: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 글로벌 프롬프트 설정 업데이트 API (관리자 전용)
@app.route('/api/admin/prompts', methods=['PUT'])
@admin_required
def update_prompts():
    """글로벌 프롬프트 설정 업데이트"""
    try:
        data = request.get_json(silent=True) or {}
        
        # 필수 필드 확인
        required_fields = ['system_prompt_template', 'welcome_message', 'ai_config']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"'{field}' 필드는 필수입니다."
                }), 400
        
        # 프롬프트 설정 업데이트
        for key, value in data.items():
            PROMPTS[key] = value
        
        # 변경사항 저장
        save_prompts()
        
        return jsonify({
            "success": True,
            "message": "프롬프트 설정이 업데이트되었습니다."
        })
    except Exception as e:
        logger.error(f"프롬프트 설정 업데이트 에러: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 게임 세션 조회 API (관리자 전용)
@app.route('/api/admin/games', methods=['GET'])
@admin_required
def get_games():
    """게임 세션 조회"""
    try:
        return jsonify({
            "success": True,
            "data": GAME_SESSIONS
        })
    except Exception as e:
        logger.error(f"게임 세션 조회 에러: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 통계 정보 API (관리자 전용)
@app.route('/api/admin/stats', methods=['GET'])
@admin_required
def get_stats():
    """통계 정보 가져오기"""
    try:
        # 통계 정보 수집
        stats = {
            "app_info": {
                "version": "1.0.0",
                "server_time": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
                "uptime": "N/A"  # 서버리스 환경에서는 제공 불가
            },
            "handler_state": {
                "active_game_sessions": len(GAME_SESSIONS),
                "games_available": len(GAMES),
                "total_game_logs": len(GAME_LOGS),
                "openai_available": bool(openai.api_key)
            },
            "categories": {}
        }
        
        # 카테고리별 통계
        categories = {}
        for game in GAMES:
            category = game.get('category', '기타')
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        stats["categories"] = categories
        
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        logger.error(f"통계 조회 에러: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 파일 시스템 경로 처리를 Vercel 환경에 맞게 수정
def get_base_path():
    """Vercel 환경과 로컬 환경에서 모두 작동하는 기본 경로 반환"""
    if os.environ.get('VERCEL'):
        # Vercel 서버리스 환경에서는 /tmp 디렉토리를 사용
        return "/tmp"
    else:
        # 로컬 환경에서는 현재 디렉토리 기준
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_file_path(file_path):
    """파일 경로를 환경에 따라 적절히 변환"""
    if os.environ.get('VERCEL'):
        # Vercel 환경에서는 상대 경로를 /tmp 아래로 변환
        base_name = os.path.basename(file_path)
        dir_name = os.path.dirname(file_path)
        
        # 디렉토리 구조 유지
        if dir_name:
            tmp_dir = os.path.join("/tmp", dir_name)
            os.makedirs(tmp_dir, exist_ok=True)
            return os.path.join(tmp_dir, base_name)
        else:
            return os.path.join("/tmp", base_name)
    else:
        # 로컬 환경에서는 그대로 사용
        return file_path

# 항목 데이터 저장 및 불러오기 함수
def save_items():
    """게임 항목 데이터를 파일에 저장"""
    try:
        # Vercel 환경에서 경로 변환
        file_path = get_file_path(ITEMS_DATA_FILE)
        logger.info(f"게임 항목 저장 시도: {file_path}")
        
        # 디렉토리 생성 확인
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(GAMES, f, ensure_ascii=False, indent=2)
        logger.info(f"게임 항목 {len(GAMES)}개가 '{file_path}'에 저장되었습니다.")
        
        # 로컬 환경에서는 원본 경로에도 저장
        if not os.environ.get('VERCEL'):
            orig_path = ITEMS_DATA_FILE
            os.makedirs(os.path.dirname(orig_path), exist_ok=True)
            with open(orig_path, 'w', encoding='utf-8') as f:
                json.dump(GAMES, f, ensure_ascii=False, indent=2)
            logger.info(f"로컬 환경: 게임 항목이 '{orig_path}'에도 저장되었습니다.")
        
        return True
    except Exception as e:
        logger.error(f"게임 항목 저장 중 오류: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def load_items():
    """파일에서 게임 항목 데이터 불러오기"""
    global GAMES
    try:
        # Vercel 환경에서 경로 변환
        file_path = get_file_path(ITEMS_DATA_FILE)
        logger.info(f"게임 항목 로드 시도: {file_path}")
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                GAMES = json.load(f)
            logger.info(f"게임 항목 {len(GAMES)}개가 '{file_path}'에서 로드되었습니다.")
        else:
            # Vercel 환경에서는 파일이 없을 수 있으므로, 데이터 폴더에서 로드 시도
            orig_path = ITEMS_DATA_FILE
            logger.info(f"원본 경로에서 게임 항목 로드 시도: {orig_path}")
            
            if os.path.exists(orig_path):
                with open(orig_path, 'r', encoding='utf-8') as f:
                    GAMES = json.load(f)
                logger.info(f"게임 항목 {len(GAMES)}개가 '{orig_path}'에서 로드되었습니다.")
                # 로드 후 /tmp에 저장
                save_items()
            else:
                # 기본 항목 데이터
                logger.info(f"게임 항목 파일이 없어 기본 데이터로 초기화합니다.")
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
                    },
                    {
                        "id": 3,
                        "title": "꿈의 직장 면접 성공하기",
                        "category": "면접",
                        "character_name": "박상현",
                        "character_setting": "당신은 대기업 면접관입니다. 기술적 지식과 문화적 적합성을 모두 평가하고 있습니다. 인재를 뽑고 싶지만 까다로운 기준이 있습니다.",
                        "max_turns": 10,
                        "win_condition": "면접관을 설득해 일자리 제안을 받는다",
                        "lose_condition": "자신의 경력이나 능력에 대해 일관성 없는 대답을 한다",
                        "difficulty": "어려움"
                    }
                ]
                logger.info(f"기본 게임 항목 {len(GAMES)}개가 로드되었습니다.")
                save_items()  # 기본 항목 저장
        return True
    except Exception as e:
        logger.error(f"게임 항목 로드 중 오류: {str(e)}")
        logger.error(traceback.format_exc())
        # 기본 항목으로 초기화
        GAMES = []
        return False

# 프롬프트 데이터 저장 및 불러오기 함수
def save_prompts():
    """게임 프롬프트 데이터를 파일에 저장"""
    try:
        file_path = get_file_path(PROMPTS_DATA_FILE)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(PROMPTS, f, ensure_ascii=False, indent=2)
        logger.info(f"게임 프롬프트가 '{file_path}'에 저장되었습니다.")
        return True
    except Exception as e:
        logger.error(f"게임 프롬프트 저장 중 오류: {str(e)}")
        return False

def load_prompts():
    """파일에서 게임 프롬프트 데이터 불러오기"""
    global PROMPTS
    try:
        file_path = get_file_path(PROMPTS_DATA_FILE)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                PROMPTS = json.load(f)
            logger.info(f"게임 프롬프트가 '{file_path}'에서 로드되었습니다.")
        else:
            # Vercel 환경에서는 파일이 없을 수 있으므로, 데이터 폴더에서 로드 시도
            orig_path = PROMPTS_DATA_FILE
            if os.path.exists(orig_path):
                with open(orig_path, 'r', encoding='utf-8') as f:
                    PROMPTS = json.load(f)
                logger.info(f"게임 프롬프트가 '{orig_path}'에서 로드되었습니다.")
                # 로드 후 /tmp에 저장
                save_prompts()
            else:
                # 기본 프롬프트 데이터
                PROMPTS = {
                    "system_prompt_template": "당신은 '상황 대처 게임'의 AI입니다.\n카테고리: {category}\n상황: {title}\n\n당신은 다음 상황에서 아래와 같은 캐릭터로 역할을 해야 합니다.\n{character_setting}\n\n규칙:\n1. 당신은 정해진 캐릭터로서 대화를 이어가야 합니다.\n2. 턴제 게임으로, 플레이어는 {max_turns}턴 안에 승리 조건을 달성해야 합니다.\n3. 현재 턴: {current_turn}/{max_turns}\n4. 승리 조건: {win_condition}\n5. 패배 조건: {lose_condition}\n6. 난이도: {difficulty}\n\n승리 조건이 충족되면 축하 메시지와 함께 게임이 종료됩니다.\n패배 조건이 충족되거나 턴을 모두 소진하면 게임이 종료됩니다.\n항상 현재 역할에 맞게 응답하세요.",
                    "welcome_message": "안녕하세요! '{title}' 상황에 오신 것을 환영합니다. 이 상황에서 여러분은 {max_turns}턴 안에 '{win_condition}'을(를) 달성해야 합니다. 대화를 통해 목표를 이루어보세요!",
                    "correct_answer_message": "축하합니다! '{win_condition}'에 성공하셨습니다!",
                    "wrong_answer_message": "아쉽게도 목표를 달성하지 못했습니다. 다음에 다시 도전해보세요.",
                    "game_end_message": "게임이 종료되었습니다. 플레이해주셔서 감사합니다.",
                    "error_messages": {
                        "game_not_found": "유효하지 않은 게임 ID입니다.",
                        "game_already_completed": "게임이 이미 종료되었습니다. 새 게임을 시작하세요.",
                        "invalid_input": "메시지가 없습니다.",
                        "server_error": "서버 오류가 발생했습니다. 다시 시도해주세요."
                    },
                    "ai_config": {
                        "model": "gpt-3.5-turbo",
                        "max_tokens": 150,
                        "temperature": 0.7
                    }
                }
                logger.info("기본 게임 프롬프트가 로드되었습니다.")
                save_prompts()  # 기본 프롬프트 저장
        return True
    except Exception as e:
        logger.error(f"게임 프롬프트 로드 중 오류: {str(e)}")
        # 기본 프롬프트로 초기화
        PROMPTS = {}
        return False

# 게임 로그 저장 및 불러오기 함수
def save_game_logs():
    """게임 로그를 파일에 저장"""
    try:
        file_path = get_file_path(GAME_LOGS_FILE)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(GAME_LOGS, f, ensure_ascii=False, indent=2)
        logger.info(f"게임 로그 {len(GAME_LOGS)}개가 '{file_path}'에 저장되었습니다.")
        return True
    except Exception as e:
        logger.error(f"게임 로그 저장 중 오류: {str(e)}")
        return False

def load_game_logs():
    """파일에서 게임 로그 불러오기"""
    global GAME_LOGS
    try:
        file_path = get_file_path(GAME_LOGS_FILE)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                GAME_LOGS = json.load(f)
            logger.info(f"게임 로그 {len(GAME_LOGS)}개가 '{file_path}'에서 로드되었습니다.")
        else:
            # Vercel 환경에서는 파일이 없을 수 있으므로, 데이터 폴더에서 로드 시도
            orig_path = GAME_LOGS_FILE
            if os.path.exists(orig_path):
                with open(orig_path, 'r', encoding='utf-8') as f:
                    GAME_LOGS = json.load(f)
                logger.info(f"게임 로그 {len(GAME_LOGS)}개가 '{orig_path}'에서 로드되었습니다.")
                # 로드 후 /tmp에 저장
                save_game_logs()
            else:
                GAME_LOGS = {}
                logger.info("게임 로그 파일이 없어 빈 로그로 초기화합니다.")
        return True
    except Exception as e:
        logger.error(f"게임 로그 로드 중 오류: {str(e)}")
        GAME_LOGS = {}
        return False

# 아이템별 프롬프트 가져오기
def load_item_prompt(item_id):
    """특정 아이템의 프롬프트 설정 가져오기"""
    try:
        # Vercel 환경에서 파일 경로 처리
        prompt_file_name = f"{item_id}.json"
        prompt_file = os.path.join('item_prompts', prompt_file_name)
        tmp_file = get_file_path(prompt_file)
        
        # 먼저 임시 디렉토리에서 확인
        if os.path.exists(tmp_file):
            with open(tmp_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        # 로컬 파일 시스템에서 확인
        if os.path.exists(prompt_file):
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_data = json.load(f)
                
            # Vercel 환경에서는 임시 디렉토리에 저장
            if os.environ.get('VERCEL'):
                os.makedirs(os.path.dirname(tmp_file), exist_ok=True)
                with open(tmp_file, 'w', encoding='utf-8') as f:
                    json.dump(prompt_data, f, ensure_ascii=False, indent=2)
                    
            return prompt_data
            
        return None
    except Exception as e:
        logger.error(f"아이템 {item_id} 프롬프트 로드 중 오류: {str(e)}")
        return None

# 데이터 로드
load_items()
load_prompts()
load_game_logs()

# OpenAI API 호출 함수
def generate_ai_response(messages, max_tokens=300):
    """
    OpenAI API를 사용하여 AI 응답 생성
    """
    try:
        if not openai.api_key:
            logger.warning("OpenAI API 키가 설정되지 않았습니다.")
            return None
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI API 호출 중 오류 발생: {str(e)}")
        return None

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
    try:
        return jsonify({
            "status": "online",
            "message": "API 서버가 정상 작동 중입니다.",
            "timestamp": int(time.time())
        })
    except Exception as e:
        logger.error(f"Health 체크 에러: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "API 서버 상태 확인 중 오류가 발생했습니다.",
            "error": str(e),
            "timestamp": int(time.time())
        }), 500

# 디버그 정보 API
@app.route('/api/debug')
def debug_info():
    """디버깅 정보 반환"""
    try:
        debug_data = {
            "active_game_sessions": len(GAME_SESSIONS),
            "games_available": len(GAMES),
            "server_time": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "openai_available": bool(openai.api_key)
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
        
        # 아이템별 프롬프트 가져오기
        item_prompt = load_item_prompt(target_game['id'])
        
        # 시스템 메시지 생성
        if item_prompt and 'system_prompt' in item_prompt:
            system_message = item_prompt['system_prompt']
        else:
            # 기본 시스템 프롬프트 템플릿 사용
            system_prompt_template = PROMPTS.get('system_prompt_template', '')
            
            # 템플릿 형식화
            system_message = system_prompt_template.format(
                title=target_game.get('title', '알 수 없는 게임'),
                category=target_game.get('category', '기타'),
                character_setting=target_game.get('character_setting', ''),
                max_turns=target_game.get('max_turns', 5),
                current_turn=1,
                win_condition=target_game.get('win_condition', ''),
                lose_condition=target_game.get('lose_condition', ''),
                difficulty=target_game.get('difficulty', '보통')
            )
        
        # 환영 메시지 생성
        welcome_message_key = f"welcome_message_{target_game.get('category', '').lower()}"
        if welcome_message_key in PROMPTS:
            welcome_message_template = PROMPTS[welcome_message_key]
        else:
            welcome_message_template = PROMPTS.get('welcome_message', '안녕하세요! 게임을 시작합니다.')
        
        welcome_message = welcome_message_template.format(
            title=target_game.get('title', '알 수 없는 게임'),
            max_turns=target_game.get('max_turns', 5),
            win_condition=target_game.get('win_condition', '')
        )
        
        # AI 설정 가져오기
        ai_config = PROMPTS.get('ai_config', {})
        if item_prompt and 'ai_config' in item_prompt:
            # 아이템별 AI 설정이 있으면 우선 적용
            for key, value in item_prompt['ai_config'].items():
                ai_config[key] = value
        
        # 게임 정보 생성
        game_info = {
            "game_id": game_id,
            "id": target_game.get('id'),
            "title": target_game.get('title', '알 수 없는 게임'),
            "category": target_game.get('category', '기타'),
            "character_name": target_game.get('character_name', 'AI'),
            "character_setting": target_game.get('character_setting', ''),
            "max_turns": target_game.get('max_turns', 5),
            "current_turn": 1,
            "win_condition": target_game.get('win_condition', ''),
            "lose_condition": target_game.get('lose_condition', ''),
            "difficulty": target_game.get('difficulty', '보통'),
            "completed": False,
            "victory": False,
            "messages": [
                {"role": "system", "content": system_message}
            ],
            "creation_time": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "welcome_message": welcome_message,
            "ai_config": ai_config
        }
        
        # 게임 세션 저장
        GAME_SESSIONS[game_id] = game_info
        
        # 게임 로그에 추가
        GAME_LOGS[game_id] = {
            "game_id": game_id,
            "target": target_game,
            "creation_time": game_info["creation_time"],
            "completed": False,
            "victory": False,
            "questions_asked": 0,
            "conversation": []
        }
        save_game_logs()
        
        # 클라이언트에 반환할 정보
        response_data = {
            "game_id": game_id,
            "title": target_game.get('title', '알 수 없는 게임'),
            "category": target_game.get('category', '기타'),
            "character_name": target_game.get('character_name', 'AI'),
            "character_setting": target_game.get('character_setting', ''),
            "max_turns": target_game.get('max_turns', 5),
            "current_turn": 1,
            "win_condition": target_game.get('win_condition', ''),
            "welcome_message": welcome_message
        }
        
        return jsonify({
            "success": True,
            "data": response_data
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
            # 시스템 메시지가 없는 경우 기본 시스템 메시지 생성
            system_message = f"""
당신은 '{game_session.get('title')}' 게임의 '{character_name}' 역할을 수행합니다.
캐릭터 설정: {game_session.get('character_setting')}
게임 카테고리: {category}
최대 턴: {max_turns}

대화를 진행하며 캐릭터 설정에 충실하게 응답해주세요.
한국어로만 응답하세요.
"""
            game_session['conversation'] = [{"role": "system", "content": system_message}]
        
        # 유저 메시지 추가
        game_session['conversation'].append({"role": "user", "content": message})
        
        # OpenAI API 호출하여 응답 생성
        ai_response = generate_ai_response(game_session['conversation'])
        
        # API 응답이 없을 경우 기본 응답으로 대체
        if ai_response is None:
            # 카테고리별 응답 생성
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
        
        # 승리 조건 확인
        if category == '플러팅' and ("010" in ai_response or "전화번호" in ai_response):
            game_session['victory'] = True
            game_session['completed'] = True
        elif category == '면접' and ("채용" in ai_response and "제안" in ai_response):
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