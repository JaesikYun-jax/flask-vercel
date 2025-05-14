# AI 추측 게임 Flask API 서버

이 저장소는 AI 추측 게임의 백엔드 API 서버를 위한 Flask 애플리케이션을 포함하고 있습니다.

## 프로젝트 구조

```
flask-vercel/
├── api/
│   ├── index.py            # Flask 애플리케이션 (메인 엔트리포인트)
│   └── ai_handler.py       # AI 핸들러 모듈
├── public/                 # 정적 파일 디렉토리
│   └── index.html          # API 문서 페이지
├── vercel.json             # Vercel 설정 파일
├── requirements.txt        # Python 패키지 목록
└── .env.example            # 환경 변수 예제 파일
```

## API 엔드포인트

- `GET /api/health`: 서버 상태 확인
- `GET /api/games`: 사용 가능한 게임 목록 조회
- `POST /api/start`: 새 게임 시작
- `POST /api/ask`: AI에게 질문하기
- `POST /api/end`: 게임 종료

## 환경 변수

코드를 실행하기 위해 다음 환경 변수가 필요합니다:

- `OPENAI_API_KEY`: OpenAI API 키
- `ADMIN_USERNAME`: 관리자 사용자명
- `ADMIN_PASSWORD`: 관리자 비밀번호

## 로컬에서 실행하기

1. Python 3.8 이상과 pip가 설치되어 있어야 합니다.
2. 필요한 패키지 설치: `pip install -r requirements.txt`
3. 환경 변수 설정: `.env.example`을 복사하여 `.env` 파일 생성 후 필요한 값 설정
4. 서버 실행: `python -m flask run`

## Vercel에 배포하기

이 저장소는 Vercel에 바로 배포할 수 있도록 구성되어 있습니다. Vercel 대시보드에서 저장소를 연결하고 필요한 환경 변수를 설정하면 됩니다. 