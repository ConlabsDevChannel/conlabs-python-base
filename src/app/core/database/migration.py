# Alembic을 이용한 데이터베이스 마이그레이션
# 기본은 수동으로 사용자가 프로젝트 레벨에서 활성화/비활성화 처리
# 기본값은 수동 (DB 편집 후 소스 수정을 기본으로)

import asyncio
import logging

from alembic import command
from alembic.config import Config


logger = logging.getLogger(__name__)


def upgrade_database() -> None:
    alembic_config = Config("alembic.ini")

    logger.info("Starting database migration")

    command.upgrade(alembic_config, "head")

    logger.info("Database migration completed")


async def auto_upgrade_database(enabled: bool) -> None:
    if not enabled:
        logger.debug("Automatic database migration is disabled")
        return

    await asyncio.to_thread(upgrade_database)