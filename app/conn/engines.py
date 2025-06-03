# Модель подключения к базе данных

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import CONFIG


class ConData:

    def __init__(self):
        self.engine = create_engine(CONFIG.db.conn.get_secret_value())
        self.session = sessionmaker(self.engine)

        try:
            self.async_engine = create_async_engine(CONFIG.db.async_conn.get_secret_value())
            self.async_session = async_sessionmaker(self.async_engine, class_=AsyncSession, expire_on_commit=False)

        except SQLAlchemyError as e:
            logger.error(e)

        except Exception as e:
            logger.exception(e)
            logger.debug(f"Не удалось создать асинхронный engine")


CONN = ConData()


if __name__ == '__main__':
    pass
