# tests/test_collection_types.py
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

class TestCollectionTypes(unittest.TestCase):
    """Lists, Sets, Sorted Sets 자료구조 API를 테스트하는 클래스"""

    def setUp(self):
        test_redis_client.flushdb()

    def tearDown(self):
        test_redis_client.flushdb()

    # ====== List 테스트 ======
    def test_list_rpush_and_rpop(self):
        """List에 RPUSH로 항목을 추가하고 RPOP으로 제거하는 테스트"""
        client.post("/lists", json={"key": "test:queue", "value": ["task1", "task2"]})
        self.assertEqual(test_redis_client.lrange("test:queue", 0, -1), ["task1", "task2"])
        
        # 마지막 항목('task2')을 꺼냅니다.
        pop_response = client.delete("/lists/test:queue/item")
        self.assertEqual(pop_response.status_code, 200)
        self.assertIn("task2", pop_response.json()["message"])
        self.assertEqual(test_redis_client.lrange("test:queue", 0, -1), ["task1"])

    def test_list_empty_pop(self):
        """비어있는 List에서 RPOP 시 404 에러 테스트"""
        response = client.delete("/lists/nonexistent:list/item")
        self.assertEqual(response.status_code, 404)
        
    # ====== Set 테스트 ======
    def test_set_add_and_read_members(self):
        """Set에 멤버를 추가하고 조회하는 테스트"""
        client.post("/sets", json={"key": "test:tags", "value": ["python", "fastapi"]})
        response = client.get("/sets/test:tags")
        self.assertEqual(response.status_code, 200)
        # Set은 순서가 없으므로 assertCountEqual로 멤버 구성만 비교합니다.
        self.assertCountEqual(response.json()["members"], ["python", "fastapi"])

    def test_set_add_duplicate_member(self):
        """Set에 중복된 멤버를 추가해도 멤버가 유일하게 유지되는지 테스트"""
        client.post("/sets", json={"key": "test:unique:users", "value": ["user:1"]})
        # 동일한 멤버를 다시 추가합니다.
        client.post("/sets", json={"key": "test:unique:users", "value": ["user:1", "user:2"]})
        # 멤버는 중복 없이 2개여야 합니다.
        self.assertEqual(test_redis_client.scard("test:unique:users"), 2)

    def test_set_remove_member(self):
        """Set에서 특정 멤버를 삭제하는 테스트"""
        members = ["apple", "banana", "cherry"]
        client.post("/sets", json={"key": "test:fruits", "value": members})
        
        # 'banana'를 삭제합니다.
        delete_response = client.delete("/sets/test:fruits/banana")
        self.assertEqual(delete_response.status_code, 200)
        self.assertCountEqual(test_redis_client.smembers("test:fruits"), ["apple", "cherry"])

    # ====== Sorted Set 테스트 ======
    def test_sorted_set_add_and_read_by_score(self):
        """Sorted Set에 스코어와 함께 멤버를 추가하고 순서대로 조회되는지 테스트"""
        client.post("/sorted-sets/test:game:scores", json={"member": "player2", "score": 200})
        client.post("/sorted-sets/test:game:scores", json={"member": "player1", "score": 100})
        client.post("/sorted-sets/test:game:scores", json={"member": "player3", "score": 300})
        
        response = client.get("/sorted-sets/test:game:scores")
        self.assertEqual(response.status_code, 200)
        # 스코어 오름차순으로 정렬되어 반환되는지 확인합니다.
        expected_ranking = [["player1", 100.0], ["player2", 200.0], ["player3", 300.0]]
        self.assertEqual(response.json()["members"], expected_ranking)

    def test_sorted_set_update_score(self):
        """Sorted Set의 기존 멤버 스코어를 업데이트하는 테스트"""
        client.post("/sorted-sets/test:ranking", json={"member": "userA", "score": 50})
        # userA의 점수를 150으로 업데이트합니다.
        update_response = client.post("/sorted-sets/test:ranking", json={"member": "userA", "score": 150})
        self.assertEqual(update_response.status_code, 200)
        
        # 점수가 올바르게 업데이트되었는지 확인합니다.
        self.assertEqual(test_redis_client.zscore("test:ranking", "userA"), 150.0)