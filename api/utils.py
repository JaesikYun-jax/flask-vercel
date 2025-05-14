import json
import os
import jwt
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from openai import OpenAI
from dotenv import load_dotenv

# 환경 변수 로드 (로컬 개발 환경용)
load_dotenv()

# JWT 서명용 비밀 키
JWT_SECRET = os.environ.get("JWT_SECRET", "your-secret-key-for-jwt-signing")

# 데이터 파일 경로
DATA_PATH = os.path.join(os.path.dirname(__file__), '../data')

# 기본 응답 생성 함수
def create_response(success=True, data=None, message=None, error=None, status_code=200):
    """일관된 형식의 API 응답을 생성합니다."""
    response = {
        "success": success
    }
    
    if data is not None:
        response["data"] = data
        
    if message is not None:
        response["message"] = message
        
    if error is not None:
        response["error"] = error
    
    return response, status_code

# JWT 토큰 검증 함수
def verify_token(auth_header):
    """
    인증 헤더에서 JWT 토큰을 추출하고 검증합니다.
    성공 시 True와 사용자 이름을 반환하고, 실패 시 False와 오류 메시지를 반환합니다.
    """
    if not auth_header:
        return False, "인증 헤더가 없습니다"
    
    try:
        # Bearer 토큰 형식에서 토큰 추출
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        else:
            token = auth_header
        
        # 토큰 디코딩 및 검증
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        
        # 만료 시간 확인
        if 'exp' in payload and datetime.utcnow().timestamp() > payload['exp']:
            return False, "토큰이 만료되었습니다"
        
        # 사용자 이름 반환
        username = payload.get('sub')
        if not username:
            return False, "토큰에 사용자 정보가 없습니다"
        
        return True, username
    except jwt.InvalidTokenError:
        return False, "유효하지 않은 토큰입니다"
    except Exception as e:
        return False, f"토큰 검증 중 오류 발생: {str(e)}"

# 관리자 인증 필요 데코레이터
def admin_required(func):
    """
    관리자 인증이 필요한 API 엔드포인트를 위한 데코레이터
    """
    def wrapper(request, response):
        # 인증 헤더 가져오기
        auth_header = None
        headers = request.get('headers', {})
        if headers:
            auth_header = headers.get('authorization') or headers.get('Authorization')
        
        # 토큰 검증
        is_valid, message = verify_token(auth_header)
        if not is_valid:
            response_data, status_code = create_response(
                success=False,
                error=f"인증 실패: {message}",
                status_code=401
            )
            return {
                "statusCode": status_code,
                "body": json.dumps(response_data),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                }
            }
        
        # 인증 성공 시 원래 함수 호출
        return func(request, response)
    
    return wrapper

# OpenAI 클라이언트 생성
def create_openai_client():
    # 여러 가능한 환경 변수 이름을 시도합니다
    possible_key_names = ['OPENAI_API_KEY', 'OPENAI_KEY', 'OPEN_AI_KEY', 'OPENAI']
    
    api_key = None
    for key_name in possible_key_names:
        api_key = os.environ.get(key_name)
        if api_key:
            break
    
    # 키가 없는 경우, 테스트 모드 API 클라이언트 반환
    if not api_key:
        print("⚠️ 경고: OpenAI API 키가 설정되지 않았습니다. 테스트 모드로 작동합니다.")
        # 테스트 모드에서는 더미 클라이언트 반환
        return MockOpenAIClient()
    
    return OpenAI(api_key=api_key)

# 테스트용 모의 OpenAI 클라이언트
class MockOpenAIClient:
    """API 키가 없을 때 사용할 테스트용 모의 클라이언트"""
    
    def __init__(self):
        self.chat = MockChatCompletion()
    
    class MockChatCompletion:
        def create(self, **kwargs):
            return {
                "choices": [
                    {
                        "message": {
                            "content": "이것은 테스트 응답입니다. 실제 API 키가 설정되지 않았습니다."
                        }
                    }
                ]
            }

# 게임 항목 로드
def load_game_items():
    try:
        with open(os.path.join(DATA_PATH, 'game_items.json'), 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # 기본 게임 항목 반환
        return [
            {
                "id": 1,
                "title": "플러팅 고수! 전화번호 따기",
                "category": "플러팅",
                "character_name": "윤지혜",
                "max_turns": 5,
                "win_condition": "상대방의 전화번호를 얻어낸다"
            },
            {
                "id": 2,
                "title": "파티에서 번호 교환하기",
                "category": "플러팅",
                "character_name": "김민준",
                "max_turns": 4,
                "win_condition": "상대방과 번호를 교환하고 다음 만남 약속을 잡는다"
            },
            {
                "id": 3,
                "title": "면접에서 목표 달성하기",
                "category": "비즈니스",
                "character_name": "이지연",
                "max_turns": 6,
                "win_condition": "면접관을 설득하고 일자리 제안받기"
            }
        ]

# 게임 항목 저장
def save_game_items(items):
    try:
        os.makedirs(DATA_PATH, exist_ok=True)
        with open(os.path.join(DATA_PATH, 'game_items.json'), 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"게임 항목 저장 중 오류: {str(e)}")
        return False 