# Модель игрока

from typing import List, Union

from fastapi import WebSocket


class Player:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
        self.score = 0
        self.lives = 5
        self.websocket: Union[WebSocket, None] = None
        self.words: List[str] = []  # Список правильных слов


if __name__ == "__main__":
    pass
