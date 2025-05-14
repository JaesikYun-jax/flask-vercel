import json
from http.server import BaseHTTPRequestHandler
from .utils import create_response

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
        
        # 필수 파라미터 확인
        game_id = body.get('game_id')
        victory = body.get('victory', False)
        
        if not game_id:
            raise ValueError("게임 ID가 필요합니다.")
        
        # 게임 평가 및 결과 생성
        # 실제로는 게임 세션 데이터를 조회하고 분석해야 함
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
        
        # 응답 데이터 생성
        end_data = {
            "game_id": game_id,
            "victory": victory,
            "message": "게임이 종료되었습니다. " + ("승리!" if victory else "다음에 다시 도전해보세요."),
            "evaluation_score": evaluation_score,
            "evaluation_message": evaluation_message.strip()
        }
        
        # 응답 생성
        response, status_code = create_response(
            success=True,
            data=end_data
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