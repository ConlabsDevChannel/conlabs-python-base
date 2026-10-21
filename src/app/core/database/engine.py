from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

# 기본 DB 호출 엔진
def create_db_engine(
    database_url: str,
    echo: bool = False
) -> AsyncEngine: # 비동기엔진
    return create_async_engine(
        url=database_url, # DBMS 접속정보 URL
        echo=echo, # SQL 로그 출력 여부
        pool_pre_ping=True, # 풀에서 꺼낼 때 유효성 확인
    )

# 중요, 엔진을 요청마다 생성해서는 안됨
# 비동기 방식이므로 await engine.dispose()로 정리