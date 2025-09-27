# tests/test_key_value_types.py
import unittest
import redis
from fastapi.testclient import TestClient
from app.main import app
from app import main

# --- 테스트 설정 (이 부분은 각 테스트 파일마다 필요합니다) ---
TEST_DB_NUM = 15
test_redis_client = redis.Redis(host='localhost', port=6379, db=TEST_DB_NUM, decode_responses=True)
main.redis_client = test_redis_client
client = TestClient(app)

class TestKeyValueTypes(unittest.TestCase):
    """Strings와 Hashes 자료구조 API를 테스트하는 클래스"""

    def setUp(self):
        test_redis_client.flushdb()

    def tearDown(self):
        test_redis_client.flushdb()

    # ====== String 테스트 ======
    def test_create_and_read_string(self):
        """String 생성 및 기본 조회 테스트"""
        client.post("/strings", json={"key": "test:user:name", "value": "Alice"})
        response = client.get("/strings/test:user:name")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["value"], "Alice")

    def test_overwrite_string(self):
        """String 덮어쓰기(업데이트) 테스트"""
        client.post("/strings", json={"key": "test:status", "value": "pending"})
        # 동일한 키에 다른 값으로 POST 요청을 보내면 덮어써져야 합니다.
        client.post("/strings", json={"key": "test:status", "value": "completed"})
        self.assertEqual(test_redis_client.get("test:status"), "completed")

    def test_read_non_existent_string(self):
        """존재하지 않는 String 조회 시 404 에러 테스트"""
        response = client.get("/strings/nonexistent:key")
        self.assertEqual(response.status_code, 404)

    def test_delete_string(self):
        """String 삭제 테스트"""
        client.post("/strings", json={"key": "test:temp:key", "value": "to_be_deleted"})
        self.assertIsNotNone(test_redis_client.get("test:temp:key"))
        
        delete_response = client.delete("/strings/test:temp:key")
        self.assertEqual(delete_response.status_code, 200)
        self.assertIsNone(test_redis_client.get("test:temp:key"))
        
    # ====== Hash 테스트 ======
    def test_create_and_read_hash(self):
        """Hash 생성 및 전체 필드 조회 테스트"""
        user_data = {"name": "Bob", "email": "bob@example.com"}
        client.post("/hashes", json={"key": "test:user:1", "value": user_data})
        
        response = client.get("/hashes/test:user:1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["value"], user_data)
        
    def test_update_and_add_hash_fields(self):
        """Hash 필드 업데이트 및 새 필드 추가 테스트"""
        client.post("/hashes", json={"key": "test:user:2", "value": {"name": "Charlie", "age": "30"}})
        # 'age' 필드는 수정하고, 'city' 필드는 새로 추가합니다.
        update_data = {"age": "31", "city": "New York"}
        client.post("/hashes", json={"key": "test:user:2", "value": update_data})
        
        expected_data = {"name": "Charlie", "age": "31", "city": "New York"}
        self.assertEqual(test_redis_client.hgetall("test:user:2"), expected_data)
        
    def test_delete_hash_field(self):
        """Hash의 특정 필드 삭제 테스트"""
        user_data = {"name": "David", "status": "active", "credits": "100"}
        client.post("/hashes", json={"key": "test:user:3", "value": user_data})
        
        # 'status' 필드를 삭제합니다.
        delete_response = client.delete("/hashes/test:user:3/status")
        self.assertEqual(delete_response.status_code, 200)
        
        # 필드가 삭제되었는지 DB에서 직접 확인합니다.
        self.assertIsNone(test_redis_client.hget("test:user:3", "status"))
        self.assertEqual(test_redis_client.hget("test:user:3", "name"), "David")