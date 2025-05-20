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



# Настройка логирования
class CreateGameRequest(BaseModel):
    player_name: str
    room_name: str = ""

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



class WsBroadcast(BaseModel):

    type: str
    grid: List[List[Union[Hex, None]]] = []
    message:Optional[str] = ""

    players: List[Union[PlayerModel, None]] = []
    current_player: Optional[str] = ""
    current_player_name: Optional[str] = ""
    is_started: bool = False
    result: Optional[SubmitWordResult] = None

class WsClickBroadcast(WsBroadcast):
    row: int
    col: int
    clicks: int

class WsInfoBroadcast(WsBroadcast):
    type: str
    message:Optional[str] = ""
    players: List[Union[PlayerModel, None]] = []


    # "players": [{"id": p.player_id, "name": p.name, "score": p.score, "lives": p.lives, "words": p.words} for p in
    #             game.players],
    # "current_player": game.players[game.current_player_index].player_id if game.players else None,
    # "current_player_name": game.players[game.current_player_index].name if game.is_started and game.players else None,
    # "is_started": True,
    # "message": f"{message}. Ход игрока {game.players[game.current_player_index].name}" if game.players else message
    #
    #
    #
    # "result": {"valid": False, "reason": "Time out"},
    #
    # "row": row,
    # "col": col,




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
