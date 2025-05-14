"""
Vercel 서버리스 함수 전용 핸들러
"""
import logging
import json
import traceback

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('vercel_handler')

try:
    from api.index import app
except ImportError:
    try:
        from index import app
    except ImportError as e:
        logger.error(f"Flask 앱 임포트 실패: {e}")
        logger.error(traceback.format_exc())

def handler(event, context):
    """
    Vercel 서버리스 함수 핸들러
    """
    logger.info("Vercel 핸들러 호출됨")
    logger.info(f"이벤트: {json.dumps(event)}")
    
    try:
        # 앱 인스턴스 확인
        if app:
            logger.info("Flask 앱 인스턴스 찾음")
            return app(event, context)
        else:
            logger.error("Flask 앱 인스턴스 없음")
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "error": "서버 초기화 실패"
                }),
                "headers": {
                    "Content-Type": "application/json"
                }
            }
    except Exception as e:
        logger.error(f"핸들러 실행 오류: {e}")
        logger.error(traceback.format_exc())
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e)
            }),
            "headers": {
                "Content-Type": "application/json"
            }
        } 