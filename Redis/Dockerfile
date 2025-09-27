# 1. 베이스 이미지 선택
FROM python:3.10-slim

# 2. 작업 디렉토리 설정
WORKDIR /code

# 3. 필요한 라이브러리 설치를 위해 requirements.txt 복사 및 설치
COPY ./app/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 4. 애플리케이션 소스 코드 복사
COPY ./app /code/app

# 5. uvicorn 서버 실행 (0.0.0.0으로 바인딩하여 외부에서 접속 가능하게 함)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]