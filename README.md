# Conlabs Python Base
## Backend base template for conlabs project

---

Python 환경 이전을 위한 프로젝트로, 모든 모듈에서 기본으로 사용할 백엔드 시스템을 구축하는데 의의를 둔 프로젝트입니다.

## Todo 샘플 시작하기

Python 3.14 이상과 uv가 필요합니다. 저장소 루트에서 실행하세요.

```sh
uv sync --group dev
```

루트에 `.env`를 만들고 개발용 DB를 설정합니다. 아래 예제는 SQLite를 사용합니다.

```dotenv
DATABASE_URL=sqlite+aiosqlite:///./sample.db
DB_MIGRATION_AUTO_UPGRADE=false
```

```sh
uv run alembic upgrade head
uv run uvicorn app.main:app --app-dir src --reload
```

Swagger UI: <http://127.0.0.1:8000/docs>

## Todo API 예제

기본 경로는 `/api/sample/todos`입니다. 아래 curl 예제는 POSIX 셸 기준입니다.
Windows PowerShell에서는 Swagger UI로 같은 요청을 실행할 수 있습니다.

```sh
# 생성: 201
curl -X POST http://127.0.0.1:8000/api/sample/todos \
  -H 'Content-Type: application/json' \
  -d '{"title":"FastAPI 샘플 읽기","description":"계층별 역할 확인"}'

# 검색 + 미완료 필터 + 정렬 + 페이징
curl 'http://127.0.0.1:8000/api/sample/todos?q=FastAPI&completed=false&sort=created_at&direction=desc&page=1&size=20'

# 단건 조회
curl http://127.0.0.1:8000/api/sample/todos/1

# 부분 수정: 생략한 필드는 유지, description의 null은 내용 삭제
curl -X PATCH http://127.0.0.1:8000/api/sample/todos/1 \
  -H 'Content-Type: application/json' \
  -d '{"completed":true,"description":null}'

# 삭제: 200, 공통 응답의 data=null
curl -X DELETE http://127.0.0.1:8000/api/sample/todos/1
```

목록 응답 예시(데이터가 없는 경우):

```json
{
  "successCode": "S",
  "resCode": "S",
  "resMessage": "정상 처리되었습니다.",
  "data": {
    "items": [],
    "page": 1,
    "size": 20,
    "total_elements": 0,
    "total_pages": 0,
    "has_next": false,
    "has_previous": false
  }
}
```

- `q`: 제목·설명에 대한 대소문자 무시 부분 검색. `%`, `_`는 일반 문자로 검색합니다. Unicode 대소문자 비교는 DB 설정에 따라 다를 수 있습니다.
- `completed`: 생략하면 전체, `true`/`false`로 완료 여부 필터.
- `sort`: `id`, `title`, `created_at`, `updated_at`. 기본값 `created_at`.
- `direction`: `asc`, `desc`. 기본값 `desc`. 정렬값이 같으면 ID를 같은 방향으로 정렬합니다.
- `page`: 1 이상. `size`: 1~100, 기본 20. 범위를 벗어난 페이지는 빈 목록과 전체 건수를 반환합니다.
- 제목은 공백을 제거한 뒤 1~200자, 설명은 최대 5,000자입니다.
- PATCH는 한 필드 이상 필요하며 `title`, `completed`에 null을 허용하지 않습니다.
- 없는 ID의 조회·수정·삭제는 404 (`TODO_NOT_FOUND`), 잘못된 입력은 422를 반환합니다.

## 샘플 구조와 트랜잭션

```text
src/app/modules/todo/
  router.py       HTTP 요청/응답과 의존성 연결
  schemas.py      입력 검증, 목록 조건, 응답 DTO
  service.py      업무 흐름과 트랜잭션 경계
  repository.py   DB 조회/변경과 flush
  models.py       SQLAlchemy 모델
```

기존 `core`의 세션, `@transactional`, 응답, 페이징을 사용합니다.
모든 공개 서비스 메서드는 keyword 인자 `session=`으로 호출합니다.
조회도 서비스에서 트랜잭션을 시작하여 UPDATE 전에 실행한 SELECT의 암시적
트랜잭션과 충돌하지 않도록 합니다. 저장소는 commit하지 않고 최상위 서비스가
성공하면 commit, 예외가 발생하면 rollback합니다. DTO는 트랜잭션 내부에서 생성합니다.

검색·정렬·LIMIT/OFFSET은 DB에서 수행합니다. 목록과 COUNT는 두 쿼리이므로
동시 쓰기 상황의 일관성은 DB 격리 수준에 따릅니다. 동시 변경 중 페이지 간 데이터가
이동할 수 있는 offset 방식이며, 대규모 데이터용 커서 페이징 예제는 포함하지 않습니다.
날짜는 DB의 timezone 없는 시간을 사용하며, `updated_at`은 ORM UPDATE 시 갱신됩니다.
인증·사용자별 소유권이 없는 학습용 샘플이므로 공개 서비스에 그대로 배포하기 전 접근 제어를 추가하세요.

## 마이그레이션과 테스트

Todo 테이블은 `sample_todos`이며 기존 초기 revision 다음에 추가됩니다.
`migrations/env.py`에서 Todo 모델을 가져와 autogenerate metadata에 등록합니다.

```sh
uv run pytest tests/modules/todo -q
uv run pytest -q
```

샘플 테스트는 독립된 메모리 SQLite DB와 임시 파일을 사용합니다.
CRUD, 검색·정렬·페이징, 입력 검증, INSERT 후 실패 시 rollback,
Alembic upgrade/downgrade 및 metadata 일치를 확인합니다.
MySQL/PostgreSQL에서의 실행 검증은 별도 환경이 필요합니다.

개발용 DB에서 마이그레이션을 되돌리는 예제(기존 Todo 데이터가 삭제됩니다):

```sh
uv run alembic downgrade 2d1b09739f06
```
