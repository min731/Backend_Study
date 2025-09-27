import os
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# FastAPI 앱 초기화
app = FastAPI()

# --- Redis 연결 설정 ---
# Docker Compose 환경에서는 서비스 이름('redis')이 호스트명이 됩니다.
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
redis_client = redis.from_url(f"redis://{REDIS_HOST}", decode_responses=True)

# --- 요청 Body 모델 정의 ---
class Item(BaseModel):
    value: str

class ScoredItem(BaseModel):
    value: str
    score: float

class HashItem(BaseModel):
    field: str
    value: str


@app.on_event("startup")
async def startup_event():
    """앱 시작 시 Redis 연결 확인"""
    try:
        await redis_client.ping()
        print("Redis에 성공적으로 연결되었습니다.")
    except Exception as e:
        print(f"Redis 연결 실패: {e}")
        # 실제 프로덕션에서는 연결 실패 시 앱을 종료하는 로직이 필요할 수 있습니다.


@app.on_event("shutdown")
async def shutdown_event():
    """앱 종료 시 Redis 연결 종료"""
    await redis_client.close()


@app.get("/")
async def read_root():
    return {"message": "FastAPI 서버와 Redis가 성공적으로 연동되었습니다!"}


# 1. String 자료구조 예제 (가장 기본적인 Key-Value)
@app.post("/string/{key}")
async def set_string(key: str, item: Item):
    await redis_client.set(key, item.value)
    return {"key": key, "value": item.value}

@app.get("/string/{key}")
async def get_string(key: str):
    value = await redis_client.get(key)
    if value is None:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"key": key, "value": value}


# 2. List 자료구조 예제 (순서가 있는 데이터 목록, 중복 허용)
@app.post("/list/{key}")
async def push_to_list(key: str, item: Item):
    await redis_client.rpush(key, item.value)
    return {"message": f"'{item.value}'가 리스트 '{key}'에 추가되었습니다."}

@app.get("/list/{key}")
async def get_list(key: str):
    values = await redis_client.lrange(key, 0, -1)
    return {"key": key, "values": values}


# 3. Set 자료구조 예제 (순서가 없는 데이터 집합, 중복 불가)
@app.post("/set/{key}")
async def add_to_set(key: str, item: Item):
    await redis_client.sadd(key, item.value)
    return {"message": f"'{item.value}'가 셋 '{key}'에 추가되었습니다."}

@app.get("/set/{key}")
async def get_set(key: str):
    values = await redis_client.smembers(key)
    return {"key": key, "values": list(values)}


# 4. Sorted Set 자료구조 예제 (점수(score)에 따라 정렬된 Set)
@app.post("/sorted-set/{key}")
async def add_to_sorted_set(key: str, item: ScoredItem):
    await redis_client.zadd(key, {item.value: item.score})
    return {"message": f"'{item.value}'(score:{item.score})가 정렬된 셋 '{key}'에 추가되었습니다."}

@app.get("/sorted-set/{key}")
async def get_sorted_set(key: str):
    # 점수가 높은 순(역순)으로 조회
    values = await redis_client.zrevrange(key, 0, -1, withscores=True)
    return {"key": key, "values": values}


# 5. Hash 자료구조 예제 (하나의 키 안에 여러 필드-값 쌍을 저장)
@app.post("/hash/{key}")
async def set_hash_field(key: str, item: HashItem):
    await redis_client.hset(key, item.field, item.value)
    return {"message": f"해시 '{key}'의 필드 '{item.field}'가 설정되었습니다."}

@app.get("/hash/{key}")
async def get_hash(key: str):
    values = await redis_client.hgetall(key)
    return {"key": key, "values": values}