from http.server import BaseHTTPRequestHandler
import json
from .utils import create_response, load_game_items

def handler(request):
    try:
        # 게임 항목 로드
        items = load_game_items()
        
        # 필요한 필드만 전송하고 난이도는 제외
        public_items = []
        for item in items:
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
        
        return {
            "statusCode": status_code,
            "body": json.dumps(response),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "GET"
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
                "Access-Control-Allow-Methods": "GET"
            }
        } 