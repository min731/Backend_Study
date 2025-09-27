
# Docker를 이용한 PostgreSQL CRUD 완벽 가이드 🐳

이 문서는 Docker를 사용하여 PostgreSQL 데이터베이스 환경을 구축하고, 테이블 생성부터 데이터 생성(Create), 조회(Read), 수정(Update), 삭제(Delete)까지의 모든 과정을 단계별로 안내합니다. 각 명령어와 SQL 구문에는 상세한 주석을 포함하여 초보자도 쉽게 따라 할 수 있도록 구성했습니다.

---

## 준비물 (Prerequisites)

-   **Docker Desktop**: 이 가이드를 진행하려면 컴퓨터에 Docker가 설치되어 있어야 합니다.
    -   [Docker 공식 홈페이지에서 다운로드](https://www.docker.com/products/docker-desktop/)

---

## 1단계: Docker로 PostgreSQL 컨테이너 실행하기

터미널(Windows의 경우 PowerShell 또는 CMD)을 열고 아래 명령어를 실행하여 PostgreSQL 서버를 컨테이너로 실행합니다.

```bash
# docker run: 새로운 컨테이너를 실행하는 명령어입니다.
# --name my-postgres: 컨테이너의 이름을 'my-postgres'로 지정합니다. 이 이름으로 컨테이너를 제어합니다.
# -e POSTGRES_PASSWORD=mysecretpassword: PostgreSQL의 관리자(postgres) 계정 비밀번호를 설정합니다. (-e는 환경변수 설정 옵션)
# -p 5432:5432: 내 컴퓨터의 5432 포트와 컨테이너의 5432 포트를 연결합니다. PostgreSQL의 기본 포트입니다.
# -d: 컨테이너를 백그라운드(detached mode)에서 실행합니다. 터미널을 계속 차지하지 않습니다.
# postgres: Docker Hub의 공식 PostgreSQL 이미지를 사용하여 컨테이너를 생성합니다.

docker run --name my-postgres -e POSTGRES_PASSWORD=mysecretpassword -p 5432:5432 -d postgres

# 현재 실행 중인 모든 도커 컨테이너의 목록을 보여줍니다.
# 목록에 'my-postgres'가 보이면 성공적으로 실행된 것입니다.
docker ps
```

## 2단계: PostgreSQL 데이터베이스에 접속하기

```bash
# docker exec -it: 실행 중인 컨테이너에 접속하여 상호작용 가능한(interactive) 터미널을 엽니다.
# my-postgres: 접속할 컨테이너의 이름입니다.
# psql -U postgres: 'postgres'라는 사용자 이름으로 psql 클라이언트를 실행합니다.

docker exec -it my-postgres psql -U postgres
```

## 3단계: 테이블과 인덱스 정의하기 (Schema)

```bash
-- users 라는 이름의 새로운 테이블을 생성합니다.
CREATE TABLE users (
    -- id: 정수 타입이며, 새로운 데이터가 추가될 때마다 자동으로 1씩 증가합니다. (SERIAL)
    -- 이 컬럼은 각 행을 고유하게 식별하는 기본 키(PRIMARY KEY) 역할을 합니다.
    id SERIAL PRIMARY KEY,

    -- username: 최대 50글자의 문자열(VARCHAR)을 저장합니다.
    -- UNIQUE: 이 컬럼의 값은 테이블 내에서 중복될 수 없습니다.
    -- NOT NULL: 이 컬럼은 비어 있을 수 없습니다. (반드시 값이 있어야 함)
    username VARCHAR(50) UNIQUE NOT NULL,

    -- email: 최대 100글자의 문자열을 저장하며, username과 마찬가지로 중복 및 NULL 값을 허용하지 않습니다.
    email VARCHAR(100) UNIQUE NOT NULL,

    -- created_at: 타임존 정보가 포함된 날짜/시간(TIMESTAMPTZ)을 저장합니다.
    -- DEFAULT now(): 데이터가 생성될 때 별도로 값을 지정하지 않으면 현재 시간이 자동으로 입력됩니다.
    created_at TIMESTAMPTZ DEFAULT now(),

    -- last_login: 마지막 로그인 시간을 저장하며, 처음에는 값이 비어있을 수 있습니다. (NULL 허용)
    last_login TIMESTAMPTZ
);
```

## 4단계: CRUD 작업 실행하기

```bash
-- INSERT INTO: 특정 테이블에 새로운 행(데이터)을 추가하는 명령어입니다.
-- users(username, email): 데이터를 추가할 컬럼을 명시합니다.
-- VALUES (...): 명시된 컬럼에 들어갈 실제 값들을 순서대로 지정합니다.

-- 1번 사용자 추가
INSERT INTO users (username, email) VALUES ('john_doe', 'john.doe@example.com');
-- 2번 사용자 추가
INSERT INTO users (username, email) VALUES ('jane_smith', 'jane.smith@example.com');
-- 3번 사용자 추가
INSERT INTO users (username, email) VALUES ('peter_pan', 'peter.pan@neverland.com');
```

```bash
-- SELECT *: 모든 컬럼을 조회하라는 의미입니다.
-- FROM users: 'users' 테이블로부터 데이터를 가져옵니다.
-- 결과: 테이블에 있는 모든 사용자 데이터가 표시됩니다.
SELECT * FROM users;

-- WHERE: 특정 조건을 만족하는 데이터만 필터링합니다.
-- username = 'jane_smith': username 컬럼의 값이 'jane_smith'인 행만 조회합니다.
SELECT * FROM users WHERE username = 'jane_smith';

-- email 컬럼으로 사용자를 조회합니다. 이 쿼리는 위에서 생성한 인덱스를 활용하여 매우 빠르게 동작합니다.
-- id, username, created_at 컬럼만 특정하여 조회합니다.
SELECT id, username, created_at FROM users WHERE email = 'john.doe@example.com';
```

```bash
-- UPDATE users: 'users' 테이블의 데이터를 수정합니다.
-- SET last_login = now(): 'last_login' 컬럼의 값을 현재 시간(now())으로 변경합니다.
-- WHERE username = 'john_doe': 수정할 대상을 'username'이 'john_doe'인 사용자로 한정합니다.
-- **주의**: WHERE 절이 없으면 테이블의 모든 행이 수정되므로 반드시 포함해야 합니다.
UPDATE users
SET last_login = now()
WHERE username = 'john_doe';

-- 수정이 잘 되었는지 확인합니다.
SELECT * FROM users WHERE username = 'john_doe';
```

```bash
-- DELETE FROM users: 'users' 테이블에서 데이터를 삭제합니다.
-- WHERE username = 'peter_pan': 삭제할 대상을 'username'이 'peter_pan'인 사용자로 한정합니다.
-- **주의**: UPDATE와 마찬가지로 WHERE 절이 없으면 테이블의 모든 데이터가 삭제됩니다.
DELETE FROM users WHERE username = 'peter_pan';

-- 삭제가 잘 되었는지 전체 데이터를 다시 확인합니다.
-- 'peter_pan' 사용자가 사라진 것을 볼 수 있습니다.
SELECT * FROM users;
```

## 5단계: 정리하기 (컨테이너 종료 및 삭제)

```bash
# docker stop: 실행 중인 컨테이너를 중지합니다.
docker stop my-postgres

# docker rm: 중지된 컨테이너를 시스템에서 완전히 삭제합니다.
# **주의**: 컨테이너를 삭제하면 그 안에 저장된 모든 데이터베이스와 데이터가 영구적으로 사라집니다.
docker rm my-postgres
```