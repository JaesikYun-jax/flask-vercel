"""
AI 추측 게임 API 서버
"""
import os
import json
import logging
import platform
import sys
import random
from flask import Flask, request, jsonify
from .utils import create_openai_client

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask 앱 초기화 - 전역 변수로 app 노출
app = Flask(__name__)

# 게임 세션 데이터 저장을 위한 임시 저장소 (실제 구현에서는 데이터베이스 사용 권장)
GAME_SESSIONS = {}

# 기본 게임 항목
DEFAULT_GAME_ITEMS = [
    {
        "id": 1,
        "title": "플러팅 고수! 전화번호 따기",
        "category": "플러팅",
        "character_name": "윤지혜",
        "character_setting": "당신은 카페에서 우연히 마주친 매력적인 사람과 대화를 시작했습니다. 그들은 친절하지만 쉽게 개인정보를 알려주지 않는 성격입니다.",
        "max_turns": 5,
        "win_condition": "상대방의 전화번호를 얻어낸다",
        "lose_condition": "턴 제한을 초과하거나 상대방이 대화를 거부한다"
    },
    {
        "id": 2,
        "title": "파티에서 번호 교환하기",
        "category": "플러팅",
        "character_name": "김민준",
        "character_setting": "당신은 친구의 파티에서 공통 관심사를 가진 사람을 만났습니다. 그들은 사교적이지만 많은 사람들에게 관심을 받고 있습니다.",
        "max_turns": 4,
        "win_condition": "상대방과 번호를 교환하고 다음 만남 약속을 잡는다",
        "lose_condition": "턴 제한을 초과하거나 상대방이 관심을 잃는다"
    },
    {
        "id": 3,
        "title": "꿈의 직장 면접 성공하기",
        "category": "면접",
        "character_name": "박상현",
        "character_setting": "당신은 꿈의 회사에서 최종 면접 단계에 진출했습니다. 면접관은 기술적 지식과 문화적 적합성을 모두 평가하고 있습니다.",
        "max_turns": 10,
        "win_condition": "면접관을 설득해 일자리 제안을 받는다",
        "lose_condition": "자신의 경력이나 능력에 대해 일관성 없는 대답을 한다"
    },
    {
        "id": 4,
        "title": "연봉 협상 마스터",
        "category": "면접",
        "character_name": "이지연",
        "character_setting": "당신은 직무 면접을 통과했고 이제 연봉 협상 단계입니다. 회사는 당신을 원하지만 예산 제약이 있습니다.",
        "max_turns": 5,
        "win_condition": "초기 제안보다 20% 이상 높은 연봉을 협상한다",
        "lose_condition": "지나치게 공격적으로 요구하여 제안이 철회된다"
    },
    {
        "id": 5,
        "title": "중고차 판매의 달인",
        "category": "물건판매",
        "character_name": "강태식",
        "character_setting": "당신은 중고차 딜러입니다. 약간의 문제가 있지만 전반적으로 상태가 좋은 중고차를 판매하려고 합니다. 강태식씨는 까다롭고 차에 대해 많은 질문을 하는 잠재 구매자입니다.",
        "max_turns": 6,
        "win_condition": "차량을 희망가보다 10% 이상 높은 가격에 판매한다",
        "lose_condition": "구매자가 거래를 거부하고 떠난다"
    },
    {
        "id": 6,
        "title": "한정판 제품 프리미엄 판매",
        "category": "물건판매",
        "character_name": "조현우",
        "character_setting": "당신은 구하기 어려운 한정판 제품을 가지고 있으며, 온라인 마켓플레이스에서 판매하려고 합니다. 구매자는 제품에 관심이 있지만 가격을 흥정하려고 합니다.",
        "max_turns": 4,
        "win_condition": "정가의 두 배 이상으로 제품을 판매한다",
        "lose_condition": "구매자가 사기를 의심하고 신고한다"
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
        # 기본 게임 아이템 직접 반환
        game_items = DEFAULT_GAME_ITEMS
        logger.info(f"게임 목록 로드 성공: {len(game_items)}개 항목")
        return jsonify({
            "success": True,
            "data": game_items
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
        logger.info(f"게임 시작 요청: {data}")
        
        # 선택된 아이템 ID (선택 사항)
        selected_item_id = data.get('item_id')
        
        # 게임 항목 로드
        all_items = DEFAULT_GAME_ITEMS
        logger.info(f"게임 항목 로드: {len(all_items)}개 항목")
        
        # 아이템 선택
        if not selected_item_id:
            # 아이템 ID가 제공되지 않은 경우 랜덤 선택
            if not all_items:
                raise ValueError("사용 가능한 게임 항목이 없습니다")
            target_item = random.choice(all_items)
            logger.info(f"랜덤 아이템 선택: {target_item['title']}")
        else:
            # 선택된 ID로 아이템 찾기
            try:
                # 정수 형식의 ID로 변환 시도
                if isinstance(selected_item_id, str) and selected_item_id.isdigit():
                    selected_item_id = int(selected_item_id)
                
                target_item = next((item for item in all_items if item['id'] == selected_item_id), None)
            except:
                target_item = None
                
            if not target_item:
                logger.error(f"선택된 게임 아이템 (ID: {selected_item_id})을 찾을 수 없습니다")
                raise ValueError(f"선택한 게임 항목(ID: {selected_item_id})을 찾을 수 없습니다")
            logger.info(f"선택된 아이템: {target_item['title']}")
        
        # 게임 ID 생성
        game_id = f"game_{os.urandom(4).hex()}"
        logger.info(f"게임 ID 생성: {game_id}")
        
        # 게임 정보 생성
        game_info = {
            "game_id": game_id,
            "item_id": target_item.get('id'),
            "title": target_item.get('title', '알 수 없는 게임'),
            "category": target_item.get('category', '기타'),
            "character_name": target_item.get('character_name', 'AI'),
            "character_setting": target_item.get('character_setting', ''),
            "win_condition": target_item.get('win_condition', '승리 조건 없음'),
            "max_turns": target_item.get('max_turns', 10),
            "current_turn": 1,
            "welcome_message": f"안녕하세요! {target_item.get('character_name', 'AI')}입니다. 게임을 시작합니다."
        }
        
        # 게임 세션 저장
        GAME_SESSIONS[game_id] = {
            'game_id': game_id,
            'item_id': target_item.get('id'),
            'title': target_item.get('title'),
            'category': target_item.get('category', '기타'),
            'character_name': target_item.get('character_name', 'AI'),
            'character_setting': target_item.get('character_setting', ''),
            'win_condition': target_item.get('win_condition'),
            'max_turns': target_item.get('max_turns', 10),
            'current_turn': 1,
            'completed': False,
            'victory': False,
            'conversation': []
        }
        
        # 응답 생성
        logger.info(f"게임 시작 성공: {game_info}")
        return jsonify({
            'success': True,
            'data': game_info
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
        
        logger.info(f"질문 처리: 게임 ID {game_id}, 메시지: {message}")
        
        if not game_id or not message:
            logger.error("game_id와 message 필드가 필요합니다")
            return jsonify({
                'success': False,
                'error': 'game_id와 message가 필요합니다.'
            }), 400
        
        # 게임 세션 데이터 확인
        game_session = GAME_SESSIONS.get(game_id)
        
        if not game_session:
            logger.warning(f"존재하지 않는 게임 ID: {game_id}")
            # 새 세션 만들기
            game_session = {
                'game_id': game_id,
                'item_id': 1,  # 기본값
                'title': '전화번호 따기',
                'category': '플러팅',
                'character_name': '윤지혜',
                'win_condition': '상대방의 전화번호를 얻어낸다',
                'max_turns': 5,
                'current_turn': 1,
                'completed': False,
                'victory': False,
                'conversation': []
            }
            GAME_SESSIONS[game_id] = game_session
            logger.info(f"새 게임 세션 생성: {game_id}")
        
        current_turn = game_session.get('current_turn', 1)
        max_turns = game_session.get('max_turns', 5)
        character_name = game_session.get('character_name', 'AI')
        category = game_session.get('category', '플러팅')
        
        # 치트키 확인
        if message == '승승리':
            logger.info(f"치트키 감지 (승리): {game_id}")
            game_session['victory'] = True
            game_session['completed'] = True
            
            return jsonify({
                'success': True,
                'data': {
                    'game_id': game_id,
                    'response': '축하합니다! 치트키를 사용하여 승리했습니다.',
                    'current_turn': current_turn,
                    'max_turns': max_turns,
                    'completed': True,
                    'victory': True
                }
            })
        elif message == '패패배':
            logger.info(f"치트키 감지 (패배): {game_id}")
            game_session['completed'] = True
            
            return jsonify({
                'success': True,
                'data': {
                    'game_id': game_id,
                    'response': '치트키를 사용하여 패배했습니다.',
                    'current_turn': current_turn,
                    'max_turns': max_turns,
                    'completed': True,
                    'victory': False
                }
            })
        
        # 대화 기록 업데이트
        if 'conversation' not in game_session:
            game_session['conversation'] = []
        
        game_session['conversation'].append({"role": "user", "content": message})
        
        # 응답 생성 - 카테고리에 따라 다른 응답 생성
        ai_response = ""
        
        # 카테고리별 응답 생성
        if category == '플러팅':
            # 전화번호/연락처 관련 패턴 확인 (승리 조건)
            if "전화" in message.lower() or "번호" in message.lower() or "연락처" in message.lower() or "만날래" in message.lower():
                ai_response = f"네! 제 전화번호는 010-1234-5678입니다. 언제든지 연락주세요! 만나면 좋을 것 같아요."
                game_session['victory'] = True
                game_session['completed'] = True
                logger.info(f"승리 조건 달성 (전화번호): {game_id}")
            elif "이름" in message.lower() or "누구" in message.lower():
                ai_response = f"제 이름은 {character_name}입니다. 만나서 반가워요!"
            elif "직업" in message.lower() or "일" in message.lower() or "뭐하" in message.lower():
                ai_response = "저는 현재 디자인 회사에서 UX 디자이너로 일하고 있어요. 사용자 경험 디자인에 관심이 많답니다."
            elif "취미" in message.lower() or "관심" in message.lower():
                ai_response = "저는 여행과 사진 찍기를 좋아해요. 최근에는 베이킹에도 관심이 생겼어요. 당신은 어떤 취미가 있나요?"
            elif "나이" in message.lower() or "몇 살" in message.lower():
                ai_response = "저는 28살이에요. 나이보다 젊게 보인다는 말을 자주 들어요. 당신은요?"
            else:
                ai_response = f"안녕하세요! 대화 재미있네요. 더 알고 싶은 것이 있으신가요?"
        elif category == '면접':
            # 면접 관련 응답
            if "경력" in message.lower() or "경험" in message.lower():
                ai_response = "저는 이 분야에서 5년간 일해왔으며, 특히 최근 3년은 팀 리더로 일하면서 프로젝트 관리 경험을 쌓았습니다."
            elif "강점" in message.lower() or "장점" in message.lower():
                ai_response = "저의 가장 큰 강점은 문제 해결 능력과 팀워크라고 생각합니다. 어려운 상황에서도 팀원들과 협력하여 목표를 달성한 경험이 많습니다."
            elif "약점" in message.lower() or "단점" in message.lower():
                ai_response = "저는 완벽주의적 성향이 있어 때로는 세부사항에 너무 집중하는 경향이 있습니다. 하지만 이를 인식하고 큰 그림을 놓치지 않도록 노력하고 있습니다."
            elif "연봉" in message.lower() or "급여" in message.lower() or "연봉" in message.lower():
                if "연봉 인상" in message.lower() or "20% 이상" in message.lower():
                    ai_response = "네, 말씀하신 연봉 인상안을 수락하겠습니다. 제안해주셔서 감사합니다!"
                    game_session['victory'] = True
                    game_session['completed'] = True
                    logger.info(f"승리 조건 달성 (연봉 협상): {game_id}")
                else:
                    ai_response = "현재 시장 상황과 제 경험을 고려할 때, 제시하신 금액보다 20% 정도 높은 연봉을 기대하고 있습니다. 가능할까요?"
            else:
                ai_response = "네, 그 부분에 대해 더 자세히 설명해 드릴 수 있습니다. 추가 질문이 있으신가요?"
        elif category == '물건판매':
            # 판매 관련 응답
            if "가격" in message.lower() or "얼마" in message.lower():
                ai_response = "이 제품의 가격은 정가보다 조금 높게 책정되어 있습니다. 품질과 희소성을 고려하면 매우 합리적인 가격이라고 생각합니다."
            elif "상태" in message.lower() or "문제" in message.lower() or "결함" in message.lower():
                ai_response = "이 제품은 전반적으로 상태가 좋습니다. 사용감은 있지만 모든 기능이 정상적으로 작동합니다."
            elif "할인" in message.lower() or "깎아" in message.lower() or "네고" in message.lower():
                if "수락" in message.lower() or "구매" in message.lower() or "살게" in message.lower():
                    ai_response = "좋습니다! 거래 성사되었습니다. 제품을 구매해 주셔서 감사합니다!"
                    game_session['victory'] = True
                    game_session['completed'] = True
                    logger.info(f"승리 조건 달성 (판매 성공): {game_id}")
                else:
                    ai_response = "죄송하지만 이미 최저가로 제시해 드린 상태입니다. 이 제품의 가치를 고려하면 정말 좋은 가격이에요."
            else:
                ai_response = "네, 이 제품에 관심을 가져주셔서 감사합니다. 더 알고 싶은 점이 있으신가요?"
        else:
            # 기본 응답
            ai_response = f"안녕하세요! 제 이름은 {character_name}입니다. 당신의 메시지 '{message}'에 대한 답변입니다. 어떻게 도와드릴까요?"
        
        # 대화 기록에 AI 응답 추가
        game_session['conversation'].append({"role": "assistant", "content": ai_response})
        
        # 턴 증가
        game_session['current_turn'] = current_turn + 1
        
        # 최대 턴 도달 시 게임 종료
        if current_turn + 1 > max_turns and not game_session['victory']:
            game_session['completed'] = True
            logger.info(f"최대 턴 도달로 게임 종료: {game_id}")
        
        # 응답 데이터
        response_data = {
            'game_id': game_id,
            'response': ai_response,
            'current_turn': game_session['current_turn'],
            'max_turns': max_turns,
            'completed': game_session['completed'],
            'victory': game_session['victory']
        }
        
        logger.info(f"응답 생성 완료: {response_data}")
        
        return jsonify({
            'success': True,
            'data': response_data
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
        
        logger.info(f"게임 종료 요청: {game_id}")
        
        if not game_id:
            return jsonify({
                'success': False,
                'error': 'game_id가 필요합니다.'
            }), 400
        
        # 게임 세션 데이터 삭제
        if game_id in GAME_SESSIONS:
            del GAME_SESSIONS[game_id]
            logger.info(f"게임 세션 삭제 완료: {game_id}")
        
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