from datetime import datetime
import json
import os
from .utils import create_response, create_openai_client

def handler(request, response):
    try:
        # OpenAI 클라이언트 상태 확인
        client_status = "unknown"
        try:
            client = create_openai_client()
            
            # API 키가 설정되었는지 확인
            if isinstance(client, object) and hasattr(client, 'chat'):
                client_status = "healthy"
            else:
                client_status = "test_mode"
        except Exception as e:
            client_status = f"error: {str(e)}"
        
        # 환경 변수 확인
        env_vars = []
        for key in os.environ:
            if key.startswith("OPENAI") or key.startswith("VERCEL") or key == "PATH":
                # 중요 키는 마스킹 처리
                value = "******"
                env_vars.append(f"{key}: {value}")
        
        # 상태 데이터 생성
        health_data = {
            "status": "ok",
            "server_time": datetime.now().isoformat(),
            "openai_client": client_status,
            "environment": "vercel",
            "api_mode": "test_mode" if client_status == "test_mode" else "production"
        }
        
        response_data, status_code = create_response(
            success=True,
            data=health_data,
            message="서버가 정상 작동 중입니다."
        )
        
        return {
            "statusCode": status_code,
            "body": json.dumps(response_data),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "GET, OPTIONS"
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
                "Access-Control-Allow-Methods": "GET, OPTIONS"
            }
        } 