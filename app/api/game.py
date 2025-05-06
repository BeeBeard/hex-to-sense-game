import random
import uuid
from typing import Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from loguru import logger
from app.models import CreateGameRequest, JoinGameRequest
from app.storage import GAMES
from app.classes import Game
from fastapi import APIRouter
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
# # Настройка логирования
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# APP = FastAPI(root_path=CONFIG.api.path)

r_game = APIRouter(tags=['API'])



@r_game.get("/", response_class=HTMLResponse)
async def get():
    logger.info("Received GET request for /")
    try:
        with open("app/static/index.html", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        logger.error(f"Error reading index.html: {e}")
        return HTMLResponse(content="Error loading page", status_code=500)

@r_game.get("/join/{game_id}", response_class=HTMLResponse)
async def join_game_page(game_id: str):
    logger.info(f"Received GET request for /join/{game_id}")
    try:
        with open("app/static/index.html", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        logger.error(f"Error reading index.html: {e}")
        return HTMLResponse(content="Error loading page", status_code=500)


@r_game.post("/create_game")
async def create_game(request: CreateGameRequest):
    player_name = request.player_name.strip() or f"Игрок_{random.randint(1000, 9999)}"
    logger.info(f"Processing create_game request for player: {player_name}")
    player_id = str(uuid.uuid4())
    game = Game(creator_id=player_id, radius=7)
    game.add_player(player_id, player_name, None)
    GAMES[game.game_id] = game
    logger.info(f"Game created: game_id={game.game_id}, player_id={player_id}, creator_id={player_id}, player_name={player_name}")
    return {"game_id": game.game_id, "player_id": player_id, "creator_id": player_id}

@r_game.post("/join_game")
async def join_game(request: JoinGameRequest):
    player_name = request.player_name.strip() or f"Игрок_{random.randint(1000, 9999)}"
    logger.info(f"Processing join_game request: game_id={request.game_id}, player_name={player_name}")
    game = GAMES.get(request.game_id.strip())
    if not game:
        logger.error(f"Game not found: {request.game_id}")
        return {"error": "Game not found"}
    if game.is_started:
        logger.error("Game has already started")
        return {"error": "Game has already started"}
    player_id = str(uuid.uuid4())
    added_player_id = game.add_player(player_id, player_name, None)
    if not added_player_id:
        logger.error("Game is full")
        return {"error": "Game is full"}
    await game.broadcast({
        "type": "info",
        "message": f"Игрок {player_name} присоединился",
        "players": [{"id": p.id, "name": p.name, "score": p.score, "lives": p.lives, "words": p.words} for p in game.players]
    })
    logger.info(f"Player joined: game_id={request.game_id}, player_id={player_id}, player_name={player_name}")
    return {"game_id": request.game_id, "player_id": player_id}


if __name__ == "__main__":
    pass
