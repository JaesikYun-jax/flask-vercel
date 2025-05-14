import json
import os
from .utils import create_response, admin_required

# 데이터 파일 경로
DATA_PATH = os.path.join(os.path.dirname(__file__), '../data')

# 프롬프트 파일 경로 가져오기
def get_prompt_file_path(item_id):
    return os.path.join(DATA_PATH, 'prompts', f'{item_id}.json')

# 프롬프트 로드
def load_item_prompt(item_id):
    try:
        file_path = get_prompt_file_path(item_id)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"프롬프트 로드 중 오류: {str(e)}")
        return None

# 프롬프트 저장
def save_item_prompt(item_id, prompt_data):
    try:
        file_path = get_prompt_file_path(item_id)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(prompt_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"프롬프트 저장 중 오류: {str(e)}")
        return False

@admin_required
def handler(request, response):
    """관리자용 프롬프트 관리 API"""
    # CORS 프리플라이트 요청 처리
    if request.get('method') == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
            }
        }
    
    # 요청 경로에서 항목 ID 추출
    path = request.get('path', '')
    item_id = None
    
    # 경로 형식: /api/admin/prompt/123
    if '/prompt/' in path:
        try:
            item_id = int(path.split('/prompt/')[1])
        except:
            item_id = None
    
    if not item_id:
        response_data, status_code = create_response(
            success=False,
            error="항목 ID가 필요합니다.",
            status_code=400
        )
        return {
            "statusCode": status_code,
            "body": json.dumps(response_data),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        }
    
    try:
        # GET: 프롬프트 조회
        if request.get('method') == "GET":
            prompt_data = load_item_prompt(item_id)
            
            if not prompt_data:
                # 기본 프롬프트 구조 제공
                prompt_data = {
                    "system_prompt": f"당신은 게임의 캐릭터입니다. 당신의 역할을 해야 합니다. 항목 ID: {item_id}",
                    "welcome_message": "안녕하세요! 무엇을 도와드릴까요?",
                    "model": "gpt-3.5-turbo",
                    "max_tokens": 200,
                    "temperature": 0.7
                }
            
            response_data, status_code = create_response(
                success=True,
                data=prompt_data
            )
        
        # POST: 프롬프트 저장
        elif request.get('method') == "POST":
            try:
                body = json.loads(request.get('body', '{}'))
            except:
                body = {}
            
            # 필수 필드 검증
            required_fields = ['system_prompt']
            for field in required_fields:
                if field not in body:
                    response_data, status_code = create_response(
                        success=False,
                        error=f"필수 필드가 누락되었습니다: {field}",
                        status_code=400
                    )
                    break
            else:
                # 저장
                if save_item_prompt(item_id, body):
                    response_data, status_code = create_response(
                        success=True,
                        data=body,
                        message=f"항목 ID {item_id}의 프롬프트가 저장되었습니다."
                    )
                else:
                    response_data, status_code = create_response(
                        success=False,
                        error="프롬프트 저장 중 오류가 발생했습니다.",
                        status_code=500
                    )
        
        # 지원하지 않는 메서드
        else:
            response_data, status_code = create_response(
                success=False,
                error=f"지원하지 않는 메서드: {request.get('method')}",
                status_code=405
            )
        
        return {
            "statusCode": status_code,
            "body": json.dumps(response_data),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
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
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
            }
        } 