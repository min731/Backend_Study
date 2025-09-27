import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Union

# --- Pydantic 모델 정의 ---
# 공통 요청 본문
class Item(BaseModel):
    key: str
    value: Union[str, int, float, List[str], Dict[str, Union[str, int, float]]]

# Sorted Set을 위한 요청 본문
class ScoreItem(BaseModel):
    member: str
    score: float

# --- FastAPI 앱 및 Redis 연결 ---
app = FastAPI(
    title="FastAPI Redis CRUD 예제",
    description="Redis의 다양한 자료구조(String, List, Hash, Set, Sorted Set)에 대한 CRUD API",
    version="1.0.0",
)

try:
    # decode_responses=True: Redis에서 받은 응답을 UTF-8로 자동 디코딩합니다.
    # db=1: 1번 데이터베이스를 사용하도록 설정합니다.
    redis_client = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)
    redis_client.ping()
    print("✅ Redis에 성공적으로 연결되었습니다.")
except redis.exceptions.ConnectionError as e:
    print(f"❌ Redis 연결에 실패했습니다: {e}")
    redis_client = None

# 앱 시작 시 Redis 연결 확인
@app.on_event("startup")
async def startup_event():
    if not redis_client:
        raise RuntimeError("Redis 연결에 실패하여 서버를 시작할 수 없습니다.")

# --- 라우터(Endpoints) 정의 ---

@app.get("/", summary="루트 경로", description="API 서버의 상태를 확인합니다.")
def read_root():
    return {"status": "FastAPI 서버가 실행 중입니다."}

# 1. Strings (문자열)
@app.post("/strings", tags=["Strings"], summary="String 생성/수정")
def create_string(item: Item):
    # Redis Query: SET <key> <value>
    redis_client.set(item.key, str(item.value))
    return {"message": f"'{item.key}' 키에 값을 저장했습니다."}

@app.get("/strings/{key}", tags=["Strings"], summary="String 조회")
def read_string(key: str):
    # Redis Query: GET <key>
    value = redis_client.get(key)
    if value is None:
        raise HTTPException(status_code=404, detail="키를 찾을 수 없습니다.")
    return {"key": key, "value": value}

@app.delete("/strings/{key}", tags=["Strings"], summary="String 삭제")
def delete_string(key: str):
    # Redis Query: DEL <key>
    if not redis_client.delete(key):
        raise HTTPException(status_code=404, detail="키를 찾을 수 없습니다.")
    return {"message": f"'{key}' 키를 삭제했습니다."}


# 2. Lists (리스트)
@app.post("/lists", tags=["Lists"], summary="List에 항목 추가 (오른쪽)")
def create_list_item(item: Item):
    if not isinstance(item.value, list):
        raise HTTPException(status_code=400, detail="값은 리스트 형태여야 합니다.")
    # Redis Query: RPUSH <key> <value1> [<value2> ...]
    redis_client.rpush(item.key, *item.value)
    return {"message": f"'{item.key}' 리스트에 항목을 추가했습니다."}

@app.get("/lists/{key}", tags=["Lists"], summary="List 전체 조회")
def read_list(key: str):
    # Redis Query: LRANGE <key> 0 -1
    values = redis_client.lrange(key, 0, -1)
    if not values:
        raise HTTPException(status_code=404, detail="리스트를 찾을 수 없습니다.")
    return {"key": key, "values": values}

@app.delete("/lists/{key}/item", tags=["Lists"], summary="List의 마지막 항목 제거 (오른쪽)")
def delete_list_item(key: str):
    # Redis Query: RPOP <key>
    value = redis_client.rpop(key)
    if value is None:
        raise HTTPException(status_code=404, detail="리스트가 비어있거나 존재하지 않습니다.")
    return {"message": f"'{key}' 리스트에서 '{value}' 항목을 제거했습니다."}


# 3. Hashes (해시)
@app.post("/hashes", tags=["Hashes"], summary="Hash 생성/수정")
def create_hash(item: Item):
    if not isinstance(item.value, dict):
        raise HTTPException(status_code=400, detail="값은 딕셔너리 형태여야 합니다.")
    # Redis Query: HSET <key> <field1> <value1> [<field2> <value2> ...]
    redis_client.hset(item.key, mapping=item.value)
    return {"message": f"'{item.key}' 해시에 필드를 저장했습니다."}

@app.get("/hashes/{key}", tags=["Hashes"], summary="Hash 전체 필드 조회")
def read_hash(key: str):
    # Redis Query: HGETALL <key>
    value = redis_client.hgetall(key)
    if not value:
        raise HTTPException(status_code=404, detail="해시를 찾을 수 없습니다.")
    return {"key": key, "value": value}

@app.delete("/hashes/{key}/{field}", tags=["Hashes"], summary="Hash의 특정 필드 삭제")
def delete_hash_field(key: str, field: str):
    # Redis Query: HDEL <key> <field>
    if not redis_client.hdel(key, field):
        raise HTTPException(status_code=404, detail="필드를 찾을 수 없습니다.")
    return {"message": f"'{key}' 해시에서 '{field}' 필드를 삭제했습니다."}


# 4. Sets (셋)
@app.post("/sets", tags=["Sets"], summary="Set에 멤버 추가")
def create_set_member(item: Item):
    if not isinstance(item.value, list):
        raise HTTPException(status_code=400, detail="값은 리스트(멤버 목록) 형태여야 합니다.")
    # Redis Query: SADD <key> <member1> [<member2> ...]
    redis_client.sadd(item.key, *item.value)
    return {"message": f"'{item.key}' 셋에 멤버를 추가했습니다."}

@app.get("/sets/{key}", tags=["Sets"], summary="Set 전체 멤버 조회")
def read_set(key: str):
    # Redis Query: SMEMBERS <key>
    members = redis_client.smembers(key)
    if not members:
        raise HTTPException(status_code=404, detail="셋을 찾을 수 없습니다.")
    return {"key": key, "members": list(members)}

@app.delete("/sets/{key}/{member}", tags=["Sets"], summary="Set의 특정 멤버 삭제")
def delete_set_member(key: str, member: str):
    # Redis Query: SREM <key> <member>
    if not redis_client.srem(key, member):
        raise HTTPException(status_code=404, detail="멤버를 찾을 수 없습니다.")
    return {"message": f"'{key}' 셋에서 '{member}' 멤버를 삭제했습니다."}


# 5. Sorted Sets (정렬된 셋)
@app.post("/sorted-sets/{key}", tags=["Sorted Sets"], summary="Sorted Set에 멤버 추가/수정")
def create_sorted_set_member(key: str, item: ScoreItem):
    # Redis Query: ZADD <key> <score> <member>
    redis_client.zadd(key, {item.member: item.score})
    return {"message": f"'{key}' 정렬된 셋에 멤버를 추가/업데이트했습니다."}

@app.get("/sorted-sets/{key}", tags=["Sorted Sets"], summary="Sorted Set 전체 멤버 조회 (스코어 기준 오름차순)")
def read_sorted_set(key: str):
    # Redis Query: ZRANGE <key> 0 -1 WITHSCORES
    members = redis_client.zrange(key, 0, -1, withscores=True)
    if not members:
        raise HTTPException(status_code=404, detail="정렬된 셋을 찾을 수 없습니다.")
    return {"key": key, "members": members}

@app.delete("/sorted-sets/{key}/{member}", tags=["Sorted Sets"], summary="Sorted Set의 특정 멤버 삭제")
def delete_sorted_set_member(key: str, member: str):
    # Redis Query: ZREM <key> <member>
    if not redis_client.zrem(key, member):
        raise HTTPException(status_code=404, detail="멤버를 찾을 수 없습니다.")
    return {"message": f"'{key}' 정렬된 셋에서 '{member}' 멤버를 삭제했습니다."}