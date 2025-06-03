# Модуль инициализации таблиц и отношений для базы данных

from typing import Annotated
from uuid import UUID

from sqlalchemy import BigInteger
from sqlalchemy import Boolean, DateTime, text, String, Integer
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy.sql import func

created = Annotated[str, mapped_column(DateTime(
    timezone=True), server_default=func.now(), nullable=False, index=True, comment='Время добавления')]

# При обновлении меняет дату обновления записи
updated = Annotated[str, mapped_column(DateTime(
    timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True, comment='Время обновления')]


# Декларативное создание
class Base(DeclarativeBase):
    type_annotation_map = {
        UUID: String(36)    # uuid.UUID → VARCHAR(36)
    }


# Таблица для хранения данных пользователей TG
class Dictionary(Base):  # Parent
    __tablename__ = "dictionary"
    __table_args__ = {'comment': 'Словарь'}

    uid = mapped_column(BigInteger, primary_key=True, unique=True, nullable=False, index=True, autoincrement=True)
    word = mapped_column(String(40), primary_key=True, unique=True, nullable=False, index=True, comment='ID пользователя')
    found_times = mapped_column(Integer, nullable=True, default=text("0"), comment='Сколько раз нашли слово')
    active = mapped_column(Boolean, server_default=text('True'), nullable=True, comment='Это слово можно найти')
    type = mapped_column(String(100), nullable=True, comment="Тип слова")
    weight = mapped_column(Integer, nullable=True, default=text("0"), comment='Сколько очков дают за слово')
    length = mapped_column(Integer, nullable=True, comment='Длина слова')
    language_code = mapped_column(String(20), nullable=True, comment='Язык')


    def __repr__(self) -> str:
        return (
            f"User("
            f"uid={self.uid!r}, "
            f"language_code={self.language_code!r})"
        )



if __name__ == '__main__':
    pass
