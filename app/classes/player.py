# Модель игрока

from typing import List, Union

from fastapi import WebSocket


class Player:
    def __init__(self, uid: str, name: str):
        self.id = uid
        self.name = name
        self.score = 0
        self.lives = 5
        self.websocket: Union[WebSocket, None] = None
        self.words: List[str] = []  # Список правильных слов

    def get_data(self):
        return {
            "id": self.id,
            "name": self.name,
            "score": self.score,
            "lives": self.lives,
            "websocket": self.websocket,
            "words": self.words,
        }


if __name__ == "__main__":
    pass
