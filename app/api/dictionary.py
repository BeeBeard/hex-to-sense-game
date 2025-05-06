import requests
from fastapi import APIRouter

from app.config import CONFIG
from app.models import YaAnswer
from app.classes import word_checker

r_dictionary = APIRouter(tags=['YANDEX DICTIONARY'])


@r_dictionary.get(f"/word")
async def check_get(word: str, lang: str = "ru-ru") -> YaAnswer:
    return word_checker.check_word(word, lang)


if __name__ == "__main__":
    pass
