# 파일명: test_main.py
# =================================================================================
# [규칙 1] 파일 이름은 'test_'로 시작해야 합니다.
# `python -m unittest discover`나 `pytest` 같은 테스트 실행 도구(Test Runner)는
# 이 규칙에 맞는 파일들만 찾아서 테스트를 수행합니다.
# 만약 파일 이름이 main_test.py 라면, 자동으로 찾아내지 못합니다.
# =================================================================================

import unittest
import redis
from fastapi.testclient import TestClient

from app.main import app
from app import main

# --- 테스트 설정 ---
TEST_DB_NUM = 15
TEST_REDIS_HOST = 'localhost'
TEST_REDIS_PORT = 6379

test_redis_client = redis.Redis(
    host=TEST_REDIS_HOST,
    port=TEST_REDIS_PORT,
    db=TEST_DB_NUM,
    decode_responses=True
)
main.redis_client = test_redis_client
client = TestClient(app)


# 클래스명: TestRedisCRUD
# =================================================================================
# [규칙 2] 테스트 클래스는 `unittest.TestCase`를 반드시 상속받아야 합니다.
# 이 상속을 통해 self.assertEqual(), self.assertRaises() 등 다양한 검증(assert) 메서드와
# setUp(), tearDown() 같은 특별한 기능을 사용할 수 있게 됩니다.
# 클래스 이름 자체를 'Test'로 시작하는 것은 필수는 아니지만, 코드를 읽는 사람이
# "아, 이건 테스트용 클래스구나"라고 바로 알 수 있게 해주는 매우 강력한 컨벤션(관례)입니다.
# =================================================================================
class TestRedisCRUD(unittest.TestCase):

    def setUp(self):
        """
        [특별 메서드] 이 메서드는 이름이 'test_'로 시작하지 않습니다.
        따라서 unittest는 이것을 개별 테스트 케이스로 실행하지 않습니다.
        'setUp'이라는 약속된 이름 덕분에, 각 테스트 메서드가 실행되기 전에
        항상 먼저 실행되는 '준비' 역할을 수행합니다.
        """
        test_redis_client.flushdb()
        print(f"\n--- Starting test: {self._testMethodName} ---")

    def tearDown(self):
        """
        [특별 메서드] 'setUp'과 마찬가지로 'test_'로 시작하지 않는 특별 메서드입니다.
        각 테스트가 끝난 후에 항상 실행되는 '정리' 역할을 합니다.
        """
        test_redis_client.flushdb()
        print("--- Finished test ---")
    
    
    # 메서드명: test_string_crud
    # =============================================================================
    # [규칙 3] 테스트 케이스 역할을 하는 메서드는 이름이 반드시 'test_'로 시작해야 합니다.
    # 테스트 실행 도구는 이 클래스 안에서 'test_'로 시작하는 모든 메서드를 찾아
    # 하나하나 독립적인 테스트로 간주하고 실행합니다.
    # 만약 이름이 string_crud_test(self) 였다면, 이 코드는 실행되지 않습니다.
    # =============================================================================
    def test_string_crud(self):
        """String 자료형의 생성, 조회, 삭제 및 실패 케이스를 테스트합니다."""
        # Create
        response = client.post("/strings", json={"key": "test:name", "value": "Alice"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(test_redis_client.get("test:name"), "Alice")

        # Read
        response = client.get("/strings/test:name")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"key": "test:name", "value": "Alice"})

        # Delete
        response = client.delete("/strings/test:name")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(test_redis_client.get("test:name"))
    
    def test_list_crud(self):
        """List 자료형의 생성, 조회, 삭제를 테스트합니다. 'test_'로 시작하므로 실행됩니다."""
        # Create
        response = client.post("/lists", json={"key": "test:fruits", "value": ["apple", "banana"]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(test_redis_client.lrange("test:fruits", 0, -1), ["apple", "banana"])
        # ... (이하 생략)

    # 만약 아래와 같이 'test_'로 시작하지 않는 헬퍼 메서드를 만든다면,
    # 이 메서드는 테스트 실행 도구에 의해 직접 실행되지 않습니다.
    # 다른 테스트 메서드 내부에서 호출하여 사용할 수는 있습니다.
    def _create_dummy_data(self, key, value):
        """이것은 테스트 케이스가 아닌, 보조(helper) 함수입니다."""
        client.post("/strings", json={"key": key, "value": value})


if __name__ == '__main__':
    unittest.main()