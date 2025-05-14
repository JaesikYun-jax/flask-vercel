import json
import re
import os
from http.server import BaseHTTPRequestHandler
from .utils import create_response, create_openai_client, load_game_items

# 게임 세션 데이터 저장을 위한 임시 저장소 (실제 구현에서는 데이터베이스 사용 권장)
GAME_SESSIONS = {}

def handler(request):
    # CORS 프리플라이트 요청 처리
    if request.get('method') == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST, OPTIONS"
            }
        }
    
    # POST 요청이 아닌 경우 오류 반환
    if request.get('method') != "POST":
        response, status_code = create_response(
            success=False,
            error="POST 요청만 지원됩니다",
            status_code=405
        )
        return {
            "statusCode": status_code,
            "body": json.dumps(response),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST, OPTIONS"
            }
        }
    
    try:
        # 요청 데이터 파싱
        try:
            body = json.loads(request.get("body", "{}"))
        except:
            # JSON 파싱 실패 시 빈 객체로 처리
            body = {}
        
        # 필수 파라미터 확인
        game_id = body.get('game_id')
        message = body.get('message', '')
        
        if not game_id:
            raise ValueError("게임 ID가 필요합니다.")
        
        if not message:
            raise ValueError("메시지가 필요합니다.")
        
        # 게임 세션 데이터 로드 또는 초기화
        game_session = GAME_SESSIONS.get(game_id, {})
        
        # 세션 데이터가 없으면 게임 아이템 정보 로드
        if not game_session:
            all_items = load_game_items()
            # game_id로 시작된 세션의 아이템 ID 찾기 (실제로는 DB에서 조회)
            # 임시로 id=1 (전화번호 따기) 사용
            game_item = next((item for item in all_items if item.get('id') == 1), None)
            
            if not game_item:
                raise ValueError("유효하지 않은 게임 세션입니다.")
            
            # 세션 초기화
            game_session = {
                'game_id': game_id,
                'item_id': game_item.get('id'),
                'title': game_item.get('title'),
                'win_condition': game_item.get('win_condition'),
                'max_turns': game_item.get('max_turns', 5),
                'current_turn': 1,
                'completed': False,
                'victory': False,
                'conversation': []
            }
            GAME_SESSIONS[game_id] = game_session
        
        # 현재 턴 가져오기
        current_turn = game_session.get('current_turn', 1)
        max_turns = game_session.get('max_turns', 5)
        
        # 치트키 확인
        victory = False
        completed = False
        
        # 치트키: '승승리' 입력 시 즉시 승리
        if message.strip() == '승승리':
            victory = True
            completed = True
            ai_response = "치트키가 입력되었습니다. 승리 조건을 달성했습니다!"
            
            # 응답 데이터 생성
            response_data = {
                "game_id": game_id,
                "response": ai_response,
                "current_turn": current_turn,
                "max_turns": max_turns,
                "completed": completed,
                "victory": victory
            }
            
            # 세션 업데이트
            game_session['completed'] = completed
            game_session['victory'] = victory
            GAME_SESSIONS[game_id] = game_session
            
            response, status_code = create_response(
                success=True,
                data=response_data
            )
            
            return {
                "statusCode": status_code,
                "body": json.dumps(response),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "POST, OPTIONS"
                }
            }
        
        # 치트키: '패패배' 입력 시 즉시 실패
        if message.strip() == '패패배':
            completed = True
            victory = False
            ai_response = "치트키가 입력되었습니다. 게임에서 패배했습니다."
            
            # 응답 데이터 생성
            response_data = {
                "game_id": game_id,
                "response": ai_response,
                "current_turn": current_turn,
                "max_turns": max_turns,
                "completed": completed,
                "victory": victory
            }
            
            # 세션 업데이트
            game_session['completed'] = completed
            game_session['victory'] = victory
            GAME_SESSIONS[game_id] = game_session
            
            response, status_code = create_response(
                success=True,
                data=response_data
            )
            
            return {
                "statusCode": status_code,
                "body": json.dumps(response),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "POST, OPTIONS"
                }
            }
        
        # 턴 제한 확인 - 이미 max_turns를 초과한 경우에만 실패로 처리
        if current_turn > max_turns:
            response_data = {
                "game_id": game_id,
                "response": "죄송합니다. 턴 제한에 도달했습니다. 게임이 종료되었습니다.",
                "current_turn": current_turn,
                "completed": True,
                "victory": False
            }
            
            response, status_code = create_response(
                success=True,
                data=response_data
            )
            
            # 세션 업데이트
            game_session['completed'] = True
            GAME_SESSIONS[game_id] = game_session
            
            return {
                "statusCode": status_code,
                "body": json.dumps(response),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "POST, OPTIONS"
                }
            }
        
        # 대화 기록 업데이트
        conversation = game_session.get('conversation', [])
        conversation.append({"role": "user", "content": message})
        
        # OpenAI 클라이언트 생성
        client = create_openai_client()
        
        try:
            # 승리 조건 확인
            win_condition = game_session.get('win_condition', '')
            
            # 기본 프롬프트
            system_prompt = f"""
            당신은 게임의 캐릭터입니다. 

            게임 제목: {game_session.get('title', 'AI 게임')}
            승리 조건: {win_condition}
            현재 턴: {current_turn}/{max_turns}

            당신은 사용자의 질문에 친절하게 답변해 주세요.
            전화번호 요청을 받으면 다음과 같은 형식으로 답변해 주세요: "제 전화번호는 010-1234-5678입니다."
            """
            
            # 대화 기록에서 적절한 형식의 메시지 생성
            messages = [{"role": "system", "content": system_prompt}]
            for msg in conversation[-5:]:  # 최근 5개 메시지만 포함
                messages.append({"role": msg.get("role"), "content": msg.get("content")})
            
            # OpenAI API로 응답 생성
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=300
            )
            
            # API 응답에서 텍스트 추출
            ai_response = response.choices[0].message.content
            
            # 대화 기록에 AI 응답 추가
            conversation.append({"role": "assistant", "content": ai_response})
            
            # 승리 조건 확인 (전화번호 포함 여부)
            victory = False
            completed = False
            
            # 전화번호 패턴 검색 (010-XXXX-XXXX 또는 010 XXXX XXXX 형식)
            phone_patterns = [
                r'010-\d{3,4}-\d{4}',  # 010-XXXX-XXXX
                r'010\s?\d{3,4}\s?\d{4}',  # 010 XXXX XXXX 또는 010XXXXXXXX
                r'전화번호[는은]?\s?01\d[-\s]?\d{3,4}[-\s]?\d{4}'  # 전화번호는 01X-XXXX-XXXX
            ]
            
            # 전화번호 패턴 확인
            if "전화번호" in win_condition.lower():
                for pattern in phone_patterns:
                    if re.search(pattern, ai_response):
                        victory = True
                        completed = True
                        break
            
            # 턴 증가
            current_turn += 1
            
            # 턴 제한 도달 시 게임 종료 (마지막 턴에서도 승리 조건 확인)
            if current_turn > max_turns and not victory:
                completed = True
            
            # 세션 업데이트
            game_session['current_turn'] = current_turn
            game_session['conversation'] = conversation
            game_session['completed'] = completed
            game_session['victory'] = victory
            GAME_SESSIONS[game_id] = game_session
            
            # 응답 데이터 생성
            response_data = {
                "game_id": game_id,
                "response": ai_response,
                "current_turn": current_turn,
                "max_turns": max_turns,
                "completed": completed,
                "victory": victory
            }
            
        except Exception as e:
            # OpenAI API 오류 시 기본 응답 제공
            ai_response = f"질문에 답변하려고 시도했지만, 응답을 생성하는 데 문제가 발생했습니다. 다시 시도해주세요."
            
            # 턴은 증가하지 않음
            response_data = {
                "game_id": game_id,
                "response": ai_response,
                "current_turn": current_turn,
                "max_turns": max_turns,
                "completed": False,
                "error": str(e)
            }
        
        # 응답 생성
        response, status_code = create_response(
            success=True,
            data=response_data
        )
        
        return {
            "statusCode": status_code,
            "body": json.dumps(response),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST, OPTIONS"
            }
        }
        
    except Exception as e:
        response, status_code = create_response(
            success=False,
            error=str(e),
            status_code=500
        )
        
        return {
            "statusCode": status_code,
            "body": json.dumps(response),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST, OPTIONS"
            }
        } 