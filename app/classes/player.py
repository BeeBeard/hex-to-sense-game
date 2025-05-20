# Модель игрока

from typing import List, Union

from fastapi import WebSocket
from app.models.models import PlayerModel

class Player:
    def __init__(self, player_id: str, name: str, lives: int = 5):
        self.player_id = player_id
        self.name = name
        self.score = 0
        self.lives = lives
        self.words: List[str] = []  # Список правильных слов
        self.websocket: Union[WebSocket, None] = None

    def get_data(self) -> PlayerModel:

        player = PlayerModel(
            player_id=self.player_id,
            name=self.name,
            score=self.score,
            lives=self.lives,
            # websocket=self.websocket,
            words=self.words,
        )

        return player



if __name__ == "__main__":
    pass
