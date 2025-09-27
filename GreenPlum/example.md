# Greenplum 분산 키 원리 완전 정복 가이드 ✅

이 문서는 `datagrip/greenplum` Docker 이미지를 사용하여 Greenplum을 설치하고, Greenplum의 핵심 성능 비결인 **'데이터 분산(Distribution)'의 원리**를 중심으로 모든 절차를 상세히 설명하는 최종 가이드입니다.

---

## 1단계: Docker로 Greenplum 컨테이너 실행하기

먼저, Greenplum 서버 역할을 할 Docker 컨테이너를 실행합니다. 이 컨테이너는 여러 개의 Greenplum 서버(세그먼트)가 하나로 묶여 동작하는 MPP(대규모 병렬 처리) 환경을 시뮬레이션합니다.

```bash
# docker run: 새로운 컨테이너를 실행하는 명령어입니다.
# -d: 컨테이너를 백그라운드(detached mode)에서 실행합니다.
# --name my-greenplum: 컨테이너에 'my-greenplum'이라는 식별하기 쉬운 이름을 부여합니다.
# -p 5432:5432: 내 컴퓨터의 5432번 포트와 컨테이너의 5432번 포트를 연결합니다.
# datagrip/greenplum: JetBrains 사에서 제공하는, 간편한 테스트용 Greenplum 이미지입니다.

docker run -d --name my-greenplum -p 5432:5432 datagrip/greenplum
```

## 2단계: Greenplum 데이터베이스에 접속하기

```bash
# docker exec -it my-greenplum /bin/bash -c "..."
# 'my-greenplum' 컨테이너 내부에서 bash 쉘을 실행하고, 큰따옴표("") 안의 명령어를 실행하라는 의미입니다.

# su - gpadmin -c '...'
# 컨테이너 내부에서 사용자 계정을 'gpadmin'으로 완전히 전환(- 플래그가 중요!)한 뒤, 작은따옴표('') 안의 명령어를 실행합니다.
# 이 과정을 통해 gpadmin 사용자에게 최적화된 환경이 모두 로드되어 psql이 정상 작동합니다.

# psql -d gpadmin
# 최종적으로 gpadmin 사용자로 gpadmin 데이터베이스에 접속합니다.

docker exec -it my-greenplum /bin/bash -c "su - gpadmin -c 'psql -d gpadmin'"
```

## 테이블 생성과 분산 키 지정의 원리

```bash
-- web_logs 라는 이름의 테이블을 생성합니다.
CREATE TABLE web_logs (
    -- log_id: 로그의 고유 식별자입니다.
    log_id BIGSERIAL,
    -- log_time: 로그가 기록된 시간입니다.
    log_time TIMESTAMPTZ DEFAULT now(),
    -- user_id: 접속한 사용자의 ID입니다. 이 컬럼이 분산의 기준이 됩니다.
    user_id INT NOT NULL,
    -- 기타 로그 정보를 저장할 컬럼들입니다.
    ip_address VARCHAR(45),
    url TEXT,
    response_time_ms INT,
    -- PRIMARY KEY (user_id, log_id): 'user_id'와 'log_id'의 조합이 고유함을 보장합니다.
    PRIMARY KEY (user_id, log_id)
)
-- DISTRIBUTED BY (user_id): 이 테이블의 모든 데이터를 'user_id' 값을 기준으로
-- 여러 서버(세그먼트)에 쪼개서 저장하라는 Greenplum의 핵심 명령입니다.
DISTRIBUTED BY (user_id);
```

### 설명 및 Greenplum 관점에서의 이유
"왜 user_id를 분산 키로 지정해야만 하는가?"

Greenplum의 목표는 수십억 건의 데이터를 여러 서버가 동시에 병렬 처리하여 분석 속도를 높이는 것입니다.

분석 목표 정의: 우리의 주된 분석 목표는 "사용자별 행동 패턴 분석"입니다. 즉, GROUP BY user_id 나 WHERE user_id = ... 와 같은 쿼리가 가장 빈번할 것입니다.

데이터 '쏠림' 방지 및 '모음' 전략: 만약 관련 없는 데이터(예: log_id)를 기준으로 데이터를 분산시키면, 특정 사용자(user_id=101)의 로그는 A, B, C 서버에 모두 흩어져 저장됩니다. 이 상태에서 "101번 사용자의 평균 응답 시간은?"이라는 쿼리를 실행하려면, Greenplum은 A, B, C 서버에 흩어진 데이터를 네트워크를 통해 한곳으로 모으는 비싼 작업을 먼저 해야 합니다. 이 '데이터 재분배(Data Redistribution)' 작업이 분산 데이터베이스의 가장 큰 성능 저하 요인입니다.

Co-location 원칙: DISTRIBUTED BY (user_id)는 이 문제를 정면으로 해결합니다. 이 규칙은 **"같은 user_id를 가진 데이터는 무슨 일이 있어도 물리적으로 같은 서버에 저장하라"**는 원칙(Co-location)을 강제합니다. 즉, 101번 사용자의 모든 로그는 A 서버에, 102번 사용자의 모든 로그는 B 서버에 모여 있게 됩니다.

성능 향상: 이제 "101번 사용자의 평균 응답 시간은?"이라는 쿼리는 네트워크 통신 없이 A 서버 단독으로 처리가 가능합니다. "모든 사용자별 평균 응답 시간은?"이라는 쿼리는 모든 서버가 각자 자기가 맡은 사용자들의 데이터만 동시에 병렬로 처리한 뒤, 최종 결과만 합치면 되므로 네트워크 부하가 거의 발생하지 않습니다.

이것이 바로 Greenplum에서 향후 분석할 데이터의 기준(Query's Granularity)을 예측하여 분산 키를 신중하게 설계해야 하는 이유입니다.

## 4단계: CRUD 및 분석 작업 실행

```bash
-- 분석할 샘플 데이터를 여러 행 추가합니다.
INSERT INTO web_logs (user_id, ip_address, url, response_time_ms) VALUES
(101, '192.168.0.10', '/home', 50),
(102, '192.168.0.25', '/products/1', 120),
(101, '192.168.0.10', '/cart', 80),
(103, '203.0.113.50', '/home', 45),
(102, '192.168.0.25', '/checkout', 250);
```
### R - Read (🔥 분석 쿼리 - Greenplum의 진가)

```bash
-- 각 사용자별 총 접속 횟수와 평균 응답시간을 계산합니다.
SELECT
    user_id,
    COUNT(*) AS access_count,
    ROUND(AVG(response_time_ms), 2) AS avg_response_time
FROM
    web_logs
GROUP BY
    user_id
ORDER BY
    access_count DESC;
```

### 설명 및 Greenplum 관점에서의 이유

이 GROUP BY user_id 쿼리는 우리가 DISTRIBUTED BY (user_id)로 설계한 이유를 증명하는 완벽한 예시입니다.

Greenplum의 모든 세그먼트 서버들은 네트워크 통신 없이 각자 자기가 가진 로그들만으로 user_id별 COUNT와 AVG 계산을 동시에 병렬로 수행합니다.

이후 계산이 끝난 작고 가벼운 중간 결과들만이 마스터 노드로 모여 최종 결과가 완성됩니다. 이 방식은 데이터 자체가 네트워크를 통해 오가는 것보다 수천, 수만 배 효율적입니다

## 5단계: 정리하기 (컨테이너 종료 및 삭제)

```bash
# 1. 'my-greenplum' 이라는 이름의 컨테이너를 중지합니다.
docker stop my-greenplum

# 2. 중지된 컨테이너를 시스템에서 완전히 삭제합니다.
docker rm my-greenplum
```