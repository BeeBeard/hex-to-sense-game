# Модуль с запросами к базе данных

from datetime import datetime

from loguru import logger
from sqlalchemy import func
from sqlalchemy import select, update
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.decl_api import DeclarativeAttributeIntercept as Dai
from app.models.models import RowDictionary
from app.conn import CONN, tables
from typing import Union


engine = CONN.engine
async_engine = CONN.async_engine
async_session = CONN.async_session


# # Добавляем данные к выбранной таблице
async def to_table(table: Dai = None, **kwargs):
    if not table or not kwargs:
        return False

    async with async_engine.connect() as session:

        try:
            logger.info(f"Добавляем/Обновляем данные для таблицы: {table.__name__}")
            kwargs["updated"] = datetime.now()
            clear_kwargs = {i: kwargs[i] for i in kwargs if i in table.__table__.columns.keys()}  # type: ignore
            # pprint.pprint(clear_kwargs)
            stmt = insert(table).values(**clear_kwargs)
            # print(stmt.compile(compile_kwargs={"literal_binds": True}))
            stmt = stmt.on_duplicate_key_update(**clear_kwargs)  # вставляем и возвращаем строку
            await session.execute(stmt)
            await session.commit()

            logger.info(f"Успешно добавили/обновили данные для таблицы: {table.__name__}")
            return True

        except SQLAlchemyError as e:

            await session.rollback()
            logger.error(f"Не удалось обновить данные для  таблицы: {table.__name__} {e}")
            return False
#
# #
# async def check_word(task_id: str) -> MessageAiBase:
#
#     if not task_id:
#         return MessageAiBase()
#
#     async with async_engine.connect() as session:
#
#         try:
#             # noinspection PyTypeChecker
#             stmt = (
#                 select(tables.AiMessage)
#                 .filter(tables.AiMessage.task_id == task_id)
#             )
#
#             result = await session.execute(stmt)
#             data = result.one_or_none()
#             if data:
#                 return MessageAiBase(
#                     uid=data.uid,
#                     task_id=data.task_id,
#                     id=data.id,
#                     model=data.model,
#                     role=data.role,
#                     content=data.content,
#                     username=data.username,
#                     user_id=data.user_id,
#                     prompt_tokens=data.prompt_tokens,
#                     completion_tokens=data.completion_tokens,
#                     total_tokens=data.total_tokens,
#                     revised_prompt=data.revised_prompt,
#                     image_url=data.image_url,
#                 )
#
#             return MessageAiBase()
#
#
#         except SQLAlchemyError as e:
#
#             await session.rollback()
#             logger.error(e)
#
#             return MessageAiBase()



def get_random_rows(limit=20, _type: str = None):
    with engine.connect() as session:

        try:
            stmt = (
                select(tables.Dictionary)


            )
            if not _type:
                stmt = stmt.where(tables.Dictionary.length >= 4)
            else:
                stmt = stmt.filter(
                    tables.Dictionary.length >= 4,
                    tables.Dictionary.type == _type,
                )

            stmt = stmt.order_by(func.random()).limit(limit)

            result = session.execute(stmt)
            data = result.all()
            if data:
                return [i.word for i in data]

            return []

        except Exception as e:
            return []


def check_update_word(word: str) -> Union[RowDictionary, bool]:

    if not word:
        return False

    with engine.connect() as session:

        try:
            stmt = (
                select(tables.Dictionary)
                .filter(tables.Dictionary.word == word)
            )

            _result = session.execute(stmt)
            data = _result.one_or_none()
            if data:
                stmt = (
                    update(tables.Dictionary)
                    .where(tables.Dictionary.word == word)
                    .values(found_times=data.found_times + 1)
                )

                session.execute(stmt)
                session.commit()

                logger.debug(f"!! {data=}")
                result = RowDictionary(
                    uid=data.uid,
                    word=data.word,
                    found_times=data.found_times,
                    active=data.active,
                    type=data.type,
                    weight=data.weight,
                    length=data.length,
                    language_code=data.language_code,
                )
                logger.debug(f"!! {result=}")

                return result

            return False

        except SQLAlchemyError as e:

            session.rollback()
            logger.error(e)

            return False

if __name__ == '__main__':
    pass
