import os
import random
import uuid

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from loguru import logger

from app.models import CreateGameRequest, JoinGameRequest
from app.storage import GM
from app.models.models import Rooms, WsInfoBroadcast

r_game = APIRouter(tags=['API'])

index_path = os.path.join("app", "static", "index.html")


@r_game.get("/", response_class=HTMLResponse)
async def get():
    logger.info("Received GET request for /")
    try:
        with open(index_path, encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        logger.error(f"Error reading index.html: {e}")
        return HTMLResponse(content="Error loading page", status_code=500)


@r_game.post("/create")
async def create_game(request: CreateGameRequest):
    player_name = request.player_name.strip() or f"Игрок_{random.randint(1000, 9999)}"
    room_name = request.room_name.strip()
    timer = request.timer
    lives = request.lives
    logger.info(f"Processing create_game request for player: {player_name}")
    player_id = str(uuid.uuid4())

    # Находим все названия комнат
    for game_id, game in GM.games.items():
        if room_name == game.room_name:
            # return HTMLResponse(content="Такая комната уже существует", status_code=500)
            return {"error": "Такая комната уже существует"}

    game = GM.create_game(creator_id=player_id, room_name=room_name, lives=lives, timer=timer, radius=7)
    game.add_player(player_id=player_id, name=request.player_name)
    # GM.games[game.game_id] = game
    logger.info(f"Game created: game_id={game.game_id}, room_name={room_name}, player_id={player_id}, creator_id={player_id}, player_name={player_name}")
    return {"game_id": game.game_id, "room_name": room_name, "player_id": player_id, "creator_id": player_id}


@r_game.get("/join/{game_id}", response_class=HTMLResponse)
async def join_game_page(game_id: str):
    logger.info(f"Received GET request for /join/{game_id}")
    try:
        with open(index_path, encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        logger.error(f"Error reading index.html: {e}")
        return HTMLResponse(content="Error loading page", status_code=500)


@r_game.post("/join")
async def join_game(request: JoinGameRequest):
    player_name = request.player_name.strip() or f"Игрок_{random.randint(1000, 9999)}"
    logger.info(f"В процессе подключения к игре:\ngame_id={request.game_id}\nplayer_name={player_name}")
    game = GM.games.get(request.game_id.strip())

    if not game:
        logger.error(f"Игра не найдена:\ngame_id={request.game_id}")
        return {"error": "Игра не найдена."}

    if game.is_started:
        logger.error("Игра уже началась.")
        return {"error": "Игра уже началась."}

    player_id = str(uuid.uuid4())
    added_player_id = game.add_player(player_id, player_name, None)

    if not added_player_id:
        logger.error("Комната уже заполнена.")
        return {"error": "Комната уже заполнена."}

    wa_broadcast = WsInfoBroadcast(
        type="info",
        message=f"Игрок {player_name} присоединился",
        players=[player.get_data() for player in game.players],
    )
    await game.broadcast(wa_broadcast.model_dump())

    logger.info(f"Игрок присоединился:\ngame_id={request.game_id}\nplayer_id={player_id}\nplayer_name={player_name}")
    return {"game_id": request.game_id, "player_id": player_id}


@r_game.get("/api/rooms")
async def get_rooms() -> Rooms:
    rooms = GM.get_active_rooms()
    return Rooms(rooms=rooms)


if __name__ == "__main__":
    pass
