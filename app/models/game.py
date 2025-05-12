from pydantic import BaseModel


# Настройка логирования
class CreateGameRequest(BaseModel):
    player_name: str
    room_name: str = ""

class JoinGameRequest(BaseModel):
    game_id: str
    player_name: str


class SubmitWordResult(BaseModel):
    word: str
    valid: bool = False
    reason: str = ""
    score: int  = 0


class Hex(BaseModel):
    number: int = 0
    x: int = 0
    y: int = 0
    letter: str = " "
    weight: int = 0
    clicks: int = 0
    show: bool = True


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
