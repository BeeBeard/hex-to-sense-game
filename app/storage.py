# Хранилище игр

from typing import Dict
import json
import random
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .classes.game import Game,  Player
from app.classes import Game
from loguru import logger
# GAMES: Dict[str, Game] = {}


class GameManager:
    def __init__(self):
        self.games: Dict[str, Game] = {}

    def create_game(self, creator_id: str, room_name: str, radius: int = 7) -> Game:
        game = Game(creator_id=creator_id, room_name=room_name, radius=radius)
        self.games[game.game_id] = game
        return game

    def get_game(self, game_id: str) -> Optional[Game]:
        return self.games.get(game_id)

    def get_active_rooms(self) -> List[dict]:

        logger.error(f"! WARNONG ! {self.games.items()}")

        return [
            {"game_id": game_id, "room_name": game.room_name, "players": len(game.players)}
            for game_id, game in self.games.items()
            if not game.is_started
        ]


GM = GameManager()
