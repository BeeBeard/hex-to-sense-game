from pydantic import BaseModel


# Настройка логирования
class CreateGameRequest(BaseModel):
    player_name: str

class JoinGameRequest(BaseModel):
    game_id: str
    player_name: str


if __name__ == "__main__":
    pass
