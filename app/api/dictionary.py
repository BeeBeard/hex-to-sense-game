from fastapi import APIRouter

from app.classes import word_checker
from app.models import YaAnswer

r_dictionary = APIRouter(tags=['YANDEX DICTIONARY'])


@r_dictionary.get(f"/word")
async def check_get(word: str, lang: str = "ru-ru") -> YaAnswer:
    return word_checker.check_word(word, lang)


if __name__ == "__main__":
    pass
