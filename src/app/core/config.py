from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

#BaseSettings: 환경변수 및 .env에서 설정을 읽고 타입 검증
class Settings(BaseSettings):
    # 여기에 작성한 변수는 .env 파일에 동일하게 작성(이 항목은 기본값이라고 보면 될 것으로 봄)
    app_name: str = "conlabs-python-base" # 프로젝트명
    app_env: str = "local" #.env
    debug: bool = True # 디버그 활성화

    # 로깅 영역
    log_level: str = "INFO"
    log_path: str = "./logs"
    log_file_name: str = "application"
    log_max_bytes: int = 50 * 1024 * 1024 # 50MiB
    log_backup_count: int = 30 # 최대 30개의 로그 파일 백업

    # db 설정
    database_url: str
    database_echo: bool = False
    # db.alembic 설정
    db_migration_auto_upgrade: bool = False # 마이그레이션 자동 실행 안함

    # httpx2 클라이언트 설정
    http_timeout: float = 30.0 # 타임아웃
    http_max_connections: int = 100 # 최대 커넥션 수
    http_max_keepalive_connections: int = 20 # 유지 커넥션 수

    #SettingsConfigDict: 설정파일을 읽는 방식 정의
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

#설정 객체를 매번 생성하지 않고 재사용
@lru_cache
def get_settings() -> Settings:
    return Settings()

# Spring Boot와 달리 Python에서는 설정 객체를 직접 생성 또는 함수로 제공하는 방식이 일반적이라고 함