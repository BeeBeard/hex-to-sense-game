# Модель игрока

from typing import List, Union

from fastapi import WebSocket
from app.models.player_model import PlayerModel

class Player:
    def __init__(self, player_id: str, name: str):
        self.player_id = player_id
        self.name = name
        self.score = 0
        self.lives = 5
        self.websocket: Union[WebSocket, None] = None
        self.words: List[str] = []  # Список правильных слов

    def get_data(self) -> dict:

        player = PlayerModel(
            player_id=self.player_id,
            name=self.name,
            score=self.score,
            lives=self.lives,
            websocket=self.websocket,
            words=self.words,
        )

        return player.model_dump()



if __name__ == "__main__":
    pass
