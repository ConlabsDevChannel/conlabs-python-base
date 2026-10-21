# 구축단계

프로젝트 구축간에 실제 사용했던 명령어 및 기술 항목을 작성합니다.

제작 과정 중 AI를 이용해 질문 및 답변을 받으며 진행하였으며, AI가 소스를 작성하는게 아닌 도움을 받기 위해 사용하였습니다.

모든 작업은 Windows 환경에서 작업하였습니다.

## 목차
> 1. 가상환경 생성
> 2. 프로젝트 최소 라이브러리 등록
> 3. 사용 폴더 구조
> 4. 프로젝트 실행 명령어

### 1. 가상환경 생성
- python 가상환경 생성(.venv)
```shell
python -m venv .venv
```
- uv 프로젝트 초기화(pyproject.toml)
```shell
uv init --bare
```

### 2. 프로젝트 최소 라이브러리 등록
#### 사용해야 할 라이브러리 리스트
- FastAPI
- uvicorn
- pydantic-settings
- concurrent-log-handler
- pytest
- httpx

#### 명령어
```shell
uv add fastapi uvicorn pydentic-settings concurrent-log-handler
```
```shell
uv add pytest httpx
```
- 테스트 중 오류 확인으로 `httpx2`를 개발용으로 저장
```shell
uv add --dev httpx2
```

### 3. 사용 폴더 구조
<pre>
pyproject.toml -- uv 설정
uv.lock -- uv 라이브러리 정보
.env -- 환경설정
src/ -- 소스 폴더
└ app/ 
  ├ __init__.py
  ├ main.py -- 시작점
  ├ core/ -- 기본 공통 설정
  └ modules/ -- 기능 폴더
tests/ -- 테스트 폴더
</pre>

### 4. 프로젝트 실행 명령어
- 실행 명령어
```shell
uv run uvicorn app.main:app --app-dir src --reload
```
- 아래 항목이 나오면 서버 실행됨
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [22392] using StatReload
INFO:     Started server process [33920]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```
- 확인은 아래 주소에서 확인
```http://127.0.0.1:8000/docs```
- 종료는 ```Ctrl+C```로 백엔드 서버 종료

### 5. 로깅 (Python logging)
- 기본 구조는 기존에 Java에서 많이 사용하던 Slf4j + Logback의 설정파일을 토대로 AI를 통해 도움
- `logback-spring.xml`을 기반으로 작업
- 이 프로젝트에서는 일단위 로깅 및 로그 파일 크기 제한을 적용하고자 함
- 날짜와 용량을 동시에 처리하기 위해 외부 라이브러리 `concurrent-log-handler`을 이용