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
            logger.error("OPENAI_API_KEY가 설정되지 않았습니다.")
            raise ValueError("OpenAI API 키가 설정되지 않았습니다. 환경 변수를 확인하세요.")
        
        return OpenAI(api_key=api_key)
    except Exception as e:
        logger.error(f"OpenAI 클라이언트 생성 오류: {str(e)}")
        raise

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