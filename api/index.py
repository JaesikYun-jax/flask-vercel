from flask import Flask, request, jsonify
import os
import sys
import json
import uuid
import logging
from datetime import datetime

# 상대 임포트를 절대 임포트로 변경
try:
    from api.ai_handler import AIHandler, create_openai_client
except ImportError:
    from ai_handler import AIHandler, create_openai_client

# 로깅 설정 강화
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask 앱 초기화
app = Flask(__name__)

# 메모리 기반 게임 데이터 저장소 (서버리스 환경에서는 각 요청마다 초기화됨)
# 실제 서비스에서는 데이터베이스 사용 권장
GAMES = {}
GAME_ITEMS = [
    {
        "id": 1,
        "title": "플러팅 고수! 전화번호 따기",
        "category": "플러팅",
        "character_name": "윤지혜",
        "max_turns": 5,
        "win_condition": "상대방의 전화번호를 얻어낸다"
    },
    {
        "id": 2,
        "title": "파티에서 번호 교환하기",
        "category": "플러팅",
        "character_name": "김민준",
        "max_turns": 4,
        "win_condition": "상대방과 번호를 교환하고 다음 만남 약속을 잡는다"
    },
    {
        "id": 3,
        "title": "면접에서 목표 달성하기",
        "category": "비즈니스",
        "character_name": "이지연",
        "max_turns": 6,
        "win_condition": "면접관을 설득하고 일자리 제안받기"
    }
]

# AI 핸들러 초기화
ai_handler = AIHandler()

# 응답 생성 함수
def create_response(success=True, data=None, message=None, error=None, status_code=200):
    """일관된 형식의 API 응답을 생성합니다."""
    response = {
        "success": success
    }
    
    if data is not None:
        response["data"] = data
    
    if message is not None:
        response["message"] = message
    
    if error is not None:
        response["error"] = error
    
    return response, status_code

@app.route('/', methods=['GET'])
def home():
    """홈 페이지"""
    return jsonify({
        "message": "AI 추측 게임 Flask 서버 - Vercel에서 실행 중",
        "status": "online",
        "version": "1.0.0"
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """서버 상태 확인"""
    return jsonify({
        "status": "healthy",
        "message": "서버가 정상적으로 작동 중입니다."
    })

@app.route('/api/games', methods=['GET'])
def get_games():
    """게임 항목 목록 제공"""
    try:
        # 게임 항목 복사 및 필요한 필드만 전송
        public_items = []
        for item in GAME_ITEMS:
            public_items.append({
                'id': item.get('id'),
                'title': item.get('title'),
                'category': item.get('category'),
                'max_turns': item.get('max_turns', 10),
                'win_condition': item.get('win_condition'),
                'character_name': item.get('character_name', 'AI')
            })
        
        response, status_code = create_response(
            success=True,
            data=public_items
        )
        
        return jsonify(response), status_code
    except Exception as e:
        logger.error(f"게임 목록 로드 오류: {str(e)}")
        response, status_code = create_response(
            success=False,
            error=str(e),
            status_code=500
        )
        return jsonify(response), status_code

@app.route('/api/start', methods=['POST'])
def start_game():
    """게임 시작"""
    try:
        # 요청 데이터 파싱
        try:
            data = request.get_json() or {}
        except:
            data = {}
        
        # 선택된 아이템 ID (선택 사항)
        selected_item_id = data.get('item_id')
        
        # 아이템 선택
        if not selected_item_id:
            # 아이템 ID가 제공되지 않은 경우 랜덤 선택
            import random
            if not GAME_ITEMS:
                return jsonify(create_response(
                    success=False,
                    error="사용 가능한 게임 항목이 없습니다",
                    status_code=404
                )[0]), 404
            target_item = random.choice(GAME_ITEMS)
        else:
            # 선택된 ID로 아이템 찾기
            target_item = next((item for item in GAME_ITEMS if item['id'] == selected_item_id), None)
            if not target_item:
                return jsonify(create_response(
                    success=False,
                    error=f"선택한 게임 항목(ID: {selected_item_id})을 찾을 수 없습니다",
                    status_code=404
                )[0]), 404
        
        # 게임 ID 생성
        game_id = str(uuid.uuid4())[:8]  # 짧은 고유 ID 생성
        
        # 최대 턴 설정
        max_turns = target_item.get('max_turns', 10)
        
        # 게임 정보 생성
        game_info = {
            "game_id": game_id,
            "title": target_item.get('title', '알 수 없는 게임'),
            "category": target_item.get('category', '기타'),
            "character_name": target_item.get('character_name', 'AI'),
            "win_condition": target_item.get('win_condition', '승리 조건 없음'),
            "max_turns": max_turns,
            "current_turn": 1,
            "completed": False,
            "victory": False,
            "conversation": [],
            "start_time": datetime.now().isoformat(),
            "welcome_message": f"안녕하세요! {target_item.get('character_name', 'AI')}입니다. 게임을 시작합니다."
        }
        
        # 게임 저장 (실제로는 서버리스 환경에서 DB에 저장해야 함)
        GAMES[game_id] = game_info
        
        # 응답 생성
        response, status_code = create_response(
            success=True,
            data=game_info
        )
        
        return jsonify(response), status_code
    
    except Exception as e:
        logger.error(f"게임 시작 오류: {str(e)}")
        response, status_code = create_response(
            success=False,
            error=str(e),
            status_code=500
        )
        return jsonify(response), status_code

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """질문 처리"""
    try:
        # 요청 데이터 파싱
        try:
            data = request.get_json() or {}
        except:
            data = {}
        
        # 필수 파라미터 확인
        game_id = data.get('game_id')
        message = data.get('message', '')
        
        if not game_id:
            return jsonify(create_response(
                success=False,
                error="게임 ID가 필요합니다.",
                status_code=400
            )[0]), 400
        
        if not message:
            return jsonify(create_response(
                success=False,
                error="메시지가 필요합니다.",
                status_code=400
            )[0]), 400
        
        # 치트키 체크: '승승리'
        if message.strip() == '승승리':
            return jsonify(create_response(
                success=True,
                data={
                    "game_id": game_id,
                    "response": "치트키가 입력되었습니다. 승리 조건을 달성했습니다!",
                    "current_turn": 1,
                    "max_turns": 5,
                    "completed": True,
                    "victory": True
                }
            )[0])
        
        # 치트키 체크: '패패배'
        if message.strip() == '패패배':
            return jsonify(create_response(
                success=True,
                data={
                    "game_id": game_id,
                    "response": "치트키가 입력되었습니다. 게임에서 패배했습니다.",
                    "current_turn": 1,
                    "max_turns": 5,
                    "completed": True,
                    "victory": False
                }
            )[0])
        
        # 게임 세션 데이터 확인 (실제로는 DB에서 로드해야 함)
        game_session = GAMES.get(game_id, None)
        if not game_session:
            # 게임 세션이 없으면 임시로 기본값 생성 (테스트용)
            game_session = {
                "game_id": game_id,
                "character_name": "AI",
                "win_condition": "상대방의 전화번호를 얻어낸다",
                "max_turns": 5,
                "current_turn": 1,
                "completed": False,
                "victory": False,
                "conversation": []
            }
            GAMES[game_id] = game_session
        
        # 게임이 이미 완료된 경우 처리
        if game_session.get('completed', False):
            return jsonify(create_response(
                success=False,
                error="게임이 이미 종료되었습니다. 새 게임을 시작하세요.",
                status_code=400
            )[0]), 400
        
        # 현재 턴 및 최대 턴 확인
        current_turn = game_session.get('current_turn', 1)
        max_turns = game_session.get('max_turns', 5)
        
        # 턴 제한 초과 확인
        if current_turn > max_turns:
            game_session['completed'] = True
            return jsonify(create_response(
                success=True,
                data={
                    "game_id": game_id,
                    "response": "턴 제한에 도달했습니다. 게임이 종료되었습니다.",
                    "current_turn": current_turn,
                    "max_turns": max_turns,
                    "completed": True,
                    "victory": False
                }
            )[0])
        
        # 대화 기록에 사용자 메시지 추가
        conversation = game_session.get('conversation', [])
        conversation.append({"role": "user", "content": message})
        
        # 시스템 프롬프트 생성
        system_prompt = f"""
        당신은 게임의 캐릭터입니다.

        게임 제목: {game_session.get('title', 'AI 게임')}
        승리 조건: {game_session.get('win_condition', '알 수 없음')}
        현재 턴: {current_turn}/{max_turns}

        당신은 사용자의 질문에 친절하게 답변해 주세요.
        전화번호 요청을 받으면 다음과 같은 형식으로 답변해 주세요: "제 전화번호는 010-1234-5678입니다."
        """
        
        # AI 응답 생성
        try:
            # OpenAI API 클라이언트 생성
            client = create_openai_client()
            
            # 간단한 대화 기록 설정
            messages = [{"role": "system", "content": system_prompt}]
            for msg in conversation[-5:]:  # 최근 5개 메시지만 포함
                messages.append({"role": msg.get("role"), "content": msg.get("content")})
            
            # API 응답 생성
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=200
            )
            
            # 응답 텍스트 추출
            ai_response = response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI 응답 생성 오류: {str(e)}")
            ai_response = "죄송합니다, 응답을 생성하는 중에 문제가 발생했습니다. 다시 시도해주세요."
        
        # 대화 기록에 AI 응답 추가
        conversation.append({"role": "assistant", "content": ai_response})
        
        # 승리 조건 확인
        victory = False
        completed = False
        
        # 전화번호 승리 조건 확인
        win_condition = game_session.get('win_condition', '').lower()
        if "전화번호" in win_condition:
            # 전화번호 패턴이 포함되어 있는지 확인
            if "010-" in ai_response or "010" in ai_response:
                victory = True
                completed = True
        
        # 턴 증가
        current_turn += 1
        
        # 턴 제한 도달 시 게임 종료 (마지막 턴에서도 승리 조건 확인)
        if current_turn > max_turns and not victory:
            completed = True
        
        # 게임 세션 업데이트
        game_session['current_turn'] = current_turn
        game_session['conversation'] = conversation
        game_session['completed'] = completed
        game_session['victory'] = victory
        
        # 응답 데이터 생성
        response_data = {
            "game_id": game_id,
            "response": ai_response,
            "current_turn": current_turn,
            "max_turns": max_turns,
            "completed": completed,
            "victory": victory
        }
        
        return jsonify(create_response(
            success=True,
            data=response_data
        )[0])
        
    except Exception as e:
        logger.error(f"질문 처리 오류: {str(e)}")
        response, status_code = create_response(
            success=False,
            error=str(e),
            status_code=500
        )
        return jsonify(response), status_code

@app.route('/api/end', methods=['POST'])
def end_game():
    """게임 종료"""
    try:
        # 요청 데이터 파싱
        try:
            data = request.get_json() or {}
        except:
            data = {}
        
        # 필수 파라미터 확인
        game_id = data.get('game_id')
        
        if not game_id:
            return jsonify(create_response(
                success=False,
                error="게임 ID가 필요합니다.",
                status_code=400
            )[0]), 400
        
        # 게임 세션 확인
        game_session = GAMES.get(game_id)
        
        # 승리 여부
        victory = data.get('victory', False)
        if game_session:
            victory = game_session.get('victory', False)
        
        # 게임 평가 및 결과 생성
        evaluation_score = 75 if victory else 45
        
        if victory:
            evaluation_message = """
            축하합니다! 게임의 승리 조건을 성공적으로 달성했습니다.
            당신의 의사소통 능력과 문제 해결 능력이 돋보였습니다.
            다양한 상황에서 상호작용하는 능력이 인상적이었습니다.
            """
        else:
            evaluation_message = """
            아쉽게도 이번에는 승리 조건을 달성하지 못했습니다.
            하지만 좋은 시도였습니다. 다음에는 상대방의 반응에 좀 더 주의를 기울이고,
            목표를 염두에 두고 대화를 이끌어보세요.
            다시 도전해보시길 권장합니다!
            """
        
        # 게임 종료 표시
        if game_session:
            game_session['completed'] = True
            game_session['end_time'] = datetime.now().isoformat()
        
        # 응답 데이터 생성
        end_data = {
            "game_id": game_id,
            "victory": victory,
            "message": "게임이 종료되었습니다. " + ("승리!" if victory else "다음에 다시 도전해보세요."),
            "evaluation_score": evaluation_score,
            "evaluation_message": evaluation_message.strip()
        }
        
        return jsonify(create_response(
            success=True,
            data=end_data
        )[0])
        
    except Exception as e:
        logger.error(f"게임 종료 오류: {str(e)}")
        response, status_code = create_response(
            success=False,
            error=str(e),
            status_code=500
        )
        return jsonify(response), status_code

# CORS 처리 추가
@app.after_request
def after_request(response):
    """CORS 헤더 추가"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# 디버깅용 라우트 추가
@app.route('/api/debug', methods=['GET'])
def debug_info():
    """디버깅 정보 제공"""
    debug_data = {
        "status": "running",
        "flask_version": Flask.__version__,
        "python_version": sys.version,
        "environment": os.environ.get('VERCEL_ENV', 'unknown'),
        "games_count": len(GAMES),
        "game_items_count": len(GAME_ITEMS),
        "timestamp": datetime.now().isoformat()
    }
    return jsonify(debug_data)

# Vercel 서버리스 함수 핸들러
def handler(event, context):
    """Vercel 서버리스 함수 핸들러"""
    logger.info("핸들러 호출됨")
    logger.info(f"이벤트: {event}")
    
    try:
        return app(event, context)
    except Exception as e:
        logger.error(f"핸들러 실행 오류: {e}")
        error_response = {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
                "success": False
            }),
            "headers": {
                "Content-Type": "application/json"
            }
        }
        logger.info(f"오류 응답 반환: {error_response}")
        return error_response

# Flask 앱을 직접 임포트하기 위한 별도 핸들러
def index_handler(event, context):
    """Vercel 서버리스 함수용 메인 핸들러"""
    logger.info("index_handler 호출됨")
    return handler(event, context)

# Vercel 서버리스 엔드포인트를 위한 함수 노출
index = app 