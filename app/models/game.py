from pydantic import BaseModel


# Настройка логирования
class CreateGameRequest(BaseModel):
    player_name: str

class JoinGameRequest(BaseModel):
    game_id: str
    player_name: str


class Hex(BaseModel):
    number: int = 0
    x: int = 0
    y: int = 0
    letter: str = " "
    weight: int = 0
    clicks: int = 0
    show: bool = True


if __name__ == "__main__":
    pass
