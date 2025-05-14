import json
import os
from datetime import datetime, timedelta
import jwt
from .utils import create_response

# 환경 변수에서 관리자 정보 가져오기 또는 기본값 사용
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin1234")

# JWT 서명용 비밀 키 (환경 변수에서 가져오거나 기본값 사용)
JWT_SECRET = os.environ.get("JWT_SECRET", "your-secret-key-for-jwt-signing")

def handler(request, response):
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
        response_data, status_code = create_response(
            success=False,
            error="POST 요청만 지원됩니다",
            status_code=405
        )
        return {
            "statusCode": status_code,
            "body": json.dumps(response_data),
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
            body = json.loads(request.get('body', '{}'))
        except:
            body = {}
        
        username = body.get('username')
        password = body.get('password')
        
        # 인증 확인
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            # JWT 토큰 생성 (유효기간 24시간)
            payload = {
                'sub': username,
                'iat': datetime.utcnow(),
                'exp': datetime.utcnow() + timedelta(hours=24)
            }
            token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
            
            # 성공 응답 반환
            response_data, status_code = create_response(
                success=True,
                data={"token": token},
                message="로그인 성공"
            )
        else:
            # 인증 실패
            response_data, status_code = create_response(
                success=False,
                error="인증 실패: 사용자 이름 또는 비밀번호가 올바르지 않습니다",
                status_code=401
            )
        
        return {
            "statusCode": status_code,
            "body": json.dumps(response_data),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST, OPTIONS"
            }
        }
        
    except Exception as e:
        response_data, status_code = create_response(
            success=False,
            error=str(e),
            status_code=500
        )
        
        return {
            "statusCode": status_code,
            "body": json.dumps(response_data),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST, OPTIONS"
            }
        } 