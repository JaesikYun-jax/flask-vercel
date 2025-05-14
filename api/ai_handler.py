import os
import json
from openai import OpenAI
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_openai_client():
    """OpenAI API 클라이언트 생성"""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY가 설정되지 않았습니다. 기본 응답을 반환합니다.")
            # 가짜 클라이언트 반환
            return MockOpenAIClient()
        
        return OpenAI(api_key=api_key)
    except Exception as e:
        logger.error(f"OpenAI 클라이언트 생성 오류: {str(e)}")
        return MockOpenAIClient()

class MockOpenAIClient:
    """API 키가 없을 때 사용할 가짜 OpenAI 클라이언트"""
    class ChatCompletions:
        def create(self, model, messages, max_tokens=None, temperature=None):
            """가짜 응답 생성"""
            logger.info("Mock OpenAI 클라이언트 사용 중")
            
            # 가짜 응답 데이터 구조
            class MockMessage:
                def __init__(self, content):
                    self.content = content
            
            class MockChoice:
                def __init__(self, content):
                    self.message = MockMessage(content)
            
            class MockResponse:
                def __init__(self, content):
                    self.choices = [MockChoice(content)]
            
            # 시스템 프롬프트와 사용자 메시지 추출
            system_prompt = None
            user_message = None
            
            for msg in messages:
                if msg["role"] == "system":
                    system_prompt = msg["content"]
                elif msg["role"] == "user":
                    user_message = msg["content"]
            
            # 간단한 응답 생성 로직
            if "전화번호" in user_message.lower():
                response = "제 전화번호는 010-1234-5678입니다."
            elif "이름" in user_message.lower():
                response = "저는 AI 어시스턴트입니다."
            elif "승리조건" in user_message.lower() or "승리 조건" in user_message.lower():
                response = "이 게임의 승리 조건은 제 전화번호를 알아내는 것입니다."
            else:
                response = "안녕하세요! 무엇을 도와드릴까요?"
            
            return MockResponse(response)
    
    def __init__(self):
        self.chat = self.ChatCompletions()

class AIHandler:
    """AI 추측 게임을 위한 AI 핸들러"""
    def __init__(self):
        """AI 핸들러 초기화"""
        self.client = create_openai_client()
    
    def generate_response(self, system_prompt, user_message, model="gpt-3.5-turbo", max_tokens=150, temperature=0.7):
        """AI 응답 생성"""
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI 응답 생성 오류: {str(e)}")
            return "AI 응답을 생성하는 중에 오류가 발생했습니다. 다시 시도해주세요."
    
    def check_victory_condition(self, game_type, conversation, victory_condition):
        """승리 조건 달성 여부 확인"""
        # 전화번호 승리 조건 확인
        if "전화번호" in victory_condition.lower():
            # 마지막 AI 응답 확인
            last_ai_response = conversation[-1]["content"] if len(conversation) > 0 and conversation[-1]["role"] == "assistant" else ""
            
            # 전화번호 패턴이 포함되어 있는지 확인
            if "010-" in last_ai_response or "010" in last_ai_response:
                return True
        
        return False 