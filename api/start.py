import json
import uuid
import random
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from .utils import create_response, load_game_items, create_openai_client

# 간단한 메모리 기반 게임 세션 저장소 (서버리스 환경에서는 매 요청마다 초기화됨)
games = {}

def handler(request):
    # CORS 프리플라이트 요청 처리
    if request.method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST, OPTIONS"
            }
        }
    
    # POST 요청이 아닌 경우 오류 반환
    if request.method != "POST":
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
        
        # 선택된 아이템 ID (선택 사항)
        selected_item_id = body.get('item_id')
        
        # 게임 항목 로드
        all_items = load_game_items()
        
        # 아이템 선택
        if not selected_item_id:
            # 아이템 ID가 제공되지 않은 경우 랜덤 선택
            if not all_items:
                raise ValueError("사용 가능한 게임 항목이 없습니다")
            target_item = random.choice(all_items)
        else:
            # 선택된 ID로 아이템 찾기
            target_item = next((item for item in all_items if item['id'] == selected_item_id), None)
            if not target_item:
                raise ValueError(f"선택한 게임 항목(ID: {selected_item_id})을 찾을 수 없습니다")
        
        # 게임 ID 생성
        game_id = str(uuid.uuid4())[:8] # 짧은 고유 ID 생성
        
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
            "welcome_message": f"안녕하세요! {target_item.get('character_name', 'AI')}입니다. 게임을 시작합니다."
        }
        
        # 응답 생성
        response, status_code = create_response(
            success=True,
            data=game_info
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