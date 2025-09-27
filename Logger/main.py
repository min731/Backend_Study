# main.py
import logging
import uuid
import yaml
from logging.config import dictConfig
from contextvars import ContextVar

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# 필요한 라이브러리: pip install fastapi uvicorn pyyaml python-json-logger
# logs 폴더를 미리 생성해주세요.

# 1. YAML 설정 파일 로드
with open("config/logging_config.yaml", "r") as f:
    config = yaml.safe_load(f)
    dictConfig(config)

# 2. ContextVar를 이용한 Request ID 컨텍스트 관리
request_id_var = ContextVar("request_id", default=None)

# 3. Request ID를 로그 레코드에 주입하는 필터
class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True

# 모든 핸들러에 필터 추가
for handler in logging.getLogger().handlers:
    handler.addFilter(RequestIdFilter())
for logger_name in config.get('loggers', {}):
    for handler in logging.getLogger(logger_name).handlers:
        handler.addFilter(RequestIdFilter())

# FastAPI 앱 생성
app = FastAPI()
logger = logging.getLogger("my_app.main")

# 4. Request ID를 생성하고 ContextVar에 저장하는 미들웨어
class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info(f"Request handled: {request.method} {request.url.path} -> {response.status_code}")
        return response

app.add_middleware(RequestIdMiddleware)

# 5. 전역 예외 처리 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.critical(
        f"처리되지 않은 예외 발생: {exc.__class__.__name__}",
        exc_info=True # Traceback을 포함
    )
    return Response("Internal Server Error", status_code=500)

# --- API Endpoints ---
from modules.bussiness_logic import process_data

@app.get("/")
async def root():
    logger.info("루트 경로가 호출되었습니다.")
    return {"message": "Advanced Logging Example"}

@app.get("/items/{item_id}")
async def get_item(item_id: str):
    logger.info(f"아이템 조회 요청 수신: {item_id}")
    result = process_data(item_id)
    return result

@app.get("/unhandled-error")
async def unhandled_error():
    # 이 에러는 try-except로 잡지 않았으므로 전역 핸들러가 처리합니다.
    result = 1 / 0
    return {"result": result}