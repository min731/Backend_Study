import time
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

# 미들웨어 클래스 또는 함수를 정의합니다.
class ProcessTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. 요청이 들어올 때 처리 (엔드포인트 실행 전)
        start_time = time.time()
        
        # 'call_next(request)'를 호출하여 다음 미들웨어나 엔드포인트로 요청을 전달합니다.
        response = await call_next(request)
        
        # 2. 응답이 나갈 때 처리 (엔드포인트 실행 후)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time) # 응답 헤더에 처리 시간 추가
        
        print(f"Request to {request.url.path} took {process_time:.4f} seconds.")
        
        return response

# 앱에 미들웨어를 추가합니다.
app.add_middleware(ProcessTimeMiddleware)

@app.get("/")
async def root():
    # 이 엔드포인트에는 시간 측정 코드가 전혀 없지만,
    # 미들웨어 덕분에 자동으로 처리 시간이 측정됩니다.
    time.sleep(0.5) # 0.5초 대기
    return {"message": "Hello World"}