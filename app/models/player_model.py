from pydantic import BaseModel
from typing import List, Union

from fastapi import WebSocket


class PlayerModel(BaseModel):
    player_id: str = ""
    name: str = ""
    score: int = 0
    lives: int  = 5
    websocket: Union[WebSocket, None] = None
    words: List[str] = []  # Список правильных слов

    class Config:
        arbitrary_types_allowed = True
