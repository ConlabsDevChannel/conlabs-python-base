# 지식정보 노트
Java 출신 개발자가 Python을 이해하기 위해 사용하는 지식 노트로, AI와의 문답 혹은 인터넷 정보를 통해 알게 된 사실을 기록합니다.

## 목차
1. 환경설정 파일을 만드는 이유
2. ```main.py```에서가 아닌 별도의 factory를 만드는 이유
3. Python logging 표준 라이브러리

---

### 1. 환경설정 파일을 만드는 이유
- Spring Boot와 달리 Python에서는 설정 객체를 직접 생성하거나 함소로 제공
- ```config.py```에서 사용한 ```pydantic-settings```는 ```application.yml```과 ```@ConfigurationPropertis```를 조합한 것과 비슷한 역할을 함

### 2. ```main.py```에서가 아닌 별도의 factory를 만드는 이유
- ```create_app()```을 이용해 향후 로깅, 예외 핸들러, 모듈 등록을 연결하고 ```main.py```를 단순하게 가져가기 위함
- 실제로는 ```main.py```에 해도 상관 없을 것으로 보임

### 3. Python logging 표준 라이브러리
- Java의 Slf4j + Logback이나 Log4j2보다 표준 라이브러리를 많이 사용한
- 인터페이스나 로그의 모든 기능을 제공
- 실제로 선택지는 아래도 있는데 이렇다고 함

| 라이브러리 | 특징 | 추천용도 |
|-----|-----|-----|
| logging | 표준 라이브러리, 외부 의존성 없음 | 범용 백엔드 |
| Loguru | 간단한 설정, 편리한 파일 로테이션 | 소규모 앱, 스크립트 |
| structlog | 구조화된 로그와 컨텍스트 처리 | 분산 시스템, JSON 로그 |
| python-json-logger | 표준 logging의 JSON 포맷터 | 로그 수집 시스템 연동 |

- 나중에 이런 라이브러리를 추가하더라도 logging을 기반으로 설정할 수 있기에 시작 레벨에서 특정 라이브러리 종속을 고집할 필요 없음

### 4. 에러 처리 중 422의 의미
- HTTP Status code 422 Unprocessable Entity

| 구분 | 400 | 422 |
|---|---|---|
| 메시지 | Bad Request | Unprocessable Entity |
| 원인 | 구문/형식 자체가 깨짐 | 구문은 맞고 의미가 맞지 않음 |
| 예시 | JSON 문법 오류, 꺠진 본문 | 형식 틀림, 필수값 누락 |
| 서버 상태 | 파싱 오류 | 파싱 성공, 검증 실패 |
참조: [HTTP 422 Unprocessable Entity - 검증 실패 400과의 차이원인 해결](https://shanael.tistory.com/452)

- 즉, Validation에서 오류가 발생했다면 422 코드가 맞다.

### 5. pytest에서의 `@pytest.fixture`
- JUnit에서의 @BeforeEach의 역할
- 현재 `conftest.py`는 이 테스트용 FastAPI를 미리 준비하는 역할
- `raise_server_exceptions=False` 이 역할은 예상치 못한 예외가 발생해도 HTTP 500 응답으로 처리하도록 함
- 테스트 과정에서 "httpx"가 "pytest"에서 "httpx2"를 권장
- `uv add --dev httpx2` 명령어로 추가