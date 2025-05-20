from typing import List, Union
from typing import Optional

from fastapi import WebSocket
from pydantic import BaseModel


# PLAYER
class PlayerModel(BaseModel):
    """Модель игрока"""

    player_id: str = ""
    name: str = ""
    score: int = 0
    lives: int  = 5
    websocket: Optional[WebSocket] = None
    words: List[str] = []  # Список правильных слов

    class Config:
        arbitrary_types_allowed = True

# HEX
class Hex(BaseModel):
    number: int = 0
    x: int = 0
    y: int = 0
    letter: str = " "
    weight: int = 0
    clicks: int = 0
    show: bool = True

# ROOM
class Room(BaseModel):
    game_id: str
    room_name: str
    players: int = 0

class Rooms(BaseModel):
    rooms: List[Room]



# Настройка логирования
class CreateGameRequest(BaseModel):
    player_name: str
    room_name: str = ""
    timer: int = 30
    lives: int = 5

class JoinGameRequest(BaseModel):
    game_id: str
    player_name: str


class SubmitWordResult(BaseModel):
    word: str = ""
    valid: bool = False
    reason: str = ""
    score: int  = 0




class GameResponce(BaseModel):
    """Ответ на создание игры и взаимодействие с полем"""

    message: Optional[str] = ""     # То что увидят игроки
    success: bool                   # Результат
    error: Optional[str] = ""       # То что уйдет в логи




# BROADCAST
class WsBroadcast(BaseModel):

    type: str
    grid: List[List[Union[Hex, None]]] = []
    message:Optional[str] = ""
    timer: int = 30

    players: List[Union[PlayerModel, None]] = []
    current_player: Optional[str] = ""
    current_player_name: Optional[str] = ""
    is_started: bool = False
    result: Optional[SubmitWordResult] = None

class WsClickBroadcast(WsBroadcast):
    row: int
    col: int
    clicks: int

class WsInfoBroadcast(BaseModel):
    type: str
    message:Optional[str] = ""
    players: List[Union[PlayerModel, None]] = []




# class GameState(BaseModel):
#     game_id: str
#     grid: List[List[Optional[Hex]]]
#     players: List[Player]
#     current_player: Optional[str] = None
#     is_started: bool
#     creator_id: str
#     current_player_name: Optional[str] = None
#     game_over: Optional[bool] = False



if __name__ == "__main__":
    pass
