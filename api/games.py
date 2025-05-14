"""
게임 목록 API 엔드포인트
"""
import json

# 샘플 게임 데이터
GAMES = [
    {
        "id": "1",
        "title": "신비한 인물 찾기",
        "category": "인물",
        "character_name": "알 수 없는 인물",
        "max_turns": 10
    },
    {
        "id": "2",
        "title": "플러팅 마스터",
        "category": "대화",
        "character_name": "신비한 상대",
        "max_turns": 5
    }
]

def handle(request, context):
    """
    게임 목록 조회 API
    """
    # CORS 헤더
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Content-Type': 'application/json'
    }
    
    # OPTIONS 요청(CORS preflight) 처리
    if request.get('method', '') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        # 게임 데이터 반환
        body = json.dumps({
            'success': True,
            'data': GAMES
        })
        
    except Exception as e:
        body = json.dumps({
            'success': False,
            'error': str(e)
        })
    
    # 응답 반환
    return {
        'statusCode': 200,
        'headers': headers,
        'body': body
    } 