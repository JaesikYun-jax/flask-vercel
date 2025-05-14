"""
헬스 체크 API 엔드포인트
"""
import json

def handle(request, context):
    """
    간단한 헬스 체크 API
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
    
    # 응답 데이터
    response_data = {
        'status': 'online',
        'message': 'API 서버가 정상 작동 중입니다.'
    }
    
    # JSON 직렬화 시도
    try:
        body = json.dumps(response_data)
    except Exception as e:
        body = json.dumps({
            'status': 'error',
            'error': f'JSON 직렬화 오류: {str(e)}'
        })
    
    # 응답 반환
    return {
        'statusCode': 200,
        'headers': headers,
        'body': body
    } 