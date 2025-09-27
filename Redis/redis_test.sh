#!/bin/bash

# 단계별 설명을 위해 echo 사용
echo "🐳 1. Redis 컨테이너를 시작합니다..."
# 컨테이너 실행 (이미 있으면 오류 메시지가 나올 수 있지만 무시하고 진행됨)
docker run --name my-redis -p 6379:6379 -d redis

# Redis-cli가 준비될 때까지 잠시 대기
sleep 3

echo -e "\n⚙️ 2. Redis 자료구조 예제를 실행합니다..."

# Redis-cli를 통해 명령어들을 한번에 실행
docker exec -i my-redis redis-cli <<EOF
# --- String 예제: UV 카운트 ---
INCR daily:uv:20250915
INCR daily:uv:20250915
GET daily:uv:20250915

# --- List 예제: 최근 검색어 ---
LPUSH search:history:user1 "redis"
LPUSH search:history:user1 "docker"
LPUSH search:history:user1 "ubuntu"
LRANGE search:history:user1 0 4

# --- Set 예제: 게시글 태그 ---
SADD post:123:tags "redis" "docker" "database"
SMEMBERS post:123:tags

# --- Sorted Set 예제: 게임 랭킹 ---
ZADD game:ranking 1500 "user:1" 2200 "user:2" 1800 "user:3"
ZREVRANGE game:ranking 0 -1 WITHSCORES

# --- Hash 예제: 사용자 프로필 ---
HSET user:1 name "Alice" email "alice@example.com" age 30
HGETALL user:1
EOF

echo -e "\n🛑 3. Redis 컨테이너를 중지합니다..."
docker stop my-redis

echo -e "\n🗑️ 4. Redis 컨테이너를 삭제합니다..."
docker rm my-redis

echo -e "\n✅ 모든 과정이 완료되었습니다."