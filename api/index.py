"""
AI 추측 게임 API 서버 - 최소 버전
"""
import os
import json
import time
from flask import Flask, jsonify

# Flask 앱 초기화
app = Flask(__name__)

# 기본 경로
@app.route('/')
def home():
    """기본 경로 처리"""
    return jsonify({
        "status": "online",
        "message": "AI 추측 게임 API 서버 작동 중",
        "version": "1.0.0",
        "timestamp": int(time.time())
    })

# 헬스 체크 API
@app.route('/api/health')
def health_check():
    """API 서버 상태 확인"""
    return jsonify({
        "status": "online",
        "message": "API 서버가 정상 작동 중입니다.",
        "timestamp": int(time.time())
    })

# 게임 목록 API
@app.route('/api/games')
def list_games():
    """게임 목록 반환"""
    games = [
        {
            "id": 1,
            "title": "플러팅 고수! 전화번호 따기",
            "category": "플러팅",
            "max_turns": 5
        },
        {
            "id": 2,
            "title": "파티에서 번호 교환하기",
            "category": "플러팅",
            "max_turns": 4
        }
    ]
    return jsonify({
        "success": True,
        "data": games
    })

# CORS 처리 함수
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    return response

# CORS Preflight 요청 처리
@app.route('/', methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path=""):
    return "", 200

# 로컬 개발용
if __name__ == '__main__':
    app.run(debug=False) 