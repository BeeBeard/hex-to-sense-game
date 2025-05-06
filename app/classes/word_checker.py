import requests
from fastapi import APIRouter

from app.config import CONFIG
from app.models import YaAnswer
from loguru import logger

def check_word(word: str, lang: str = "ru-ru") -> YaAnswer:

    try:
        yandex_api = "https://dictionary.yandex.net/api/v1/dicservice.json/lookup?"

        url = f"{yandex_api}key={CONFIG.yandex.token}&lang={lang}&text={word}"

        responce = requests.get(url)

        print(responce)
        content = responce.content.decode("utf-8")
        print(content)
        ya_answer = YaAnswer.model_validate_json(responce.content)

        return ya_answer

    except Exception as e:

        logger.error(e)
        return YaAnswer()


if __name__ == "__main__":
    pass
