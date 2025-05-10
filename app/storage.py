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

# GAMES: Dict[str, Game] = {}


class GameManager:
    def __init__(self):
        self.games: Dict[str, Game] = {}

    def create_game(self, creator_id: str, radius: int = 7) -> Game:
        game = Game(creator_id)
        self.games[game.game_id] = game
        return game

    def get_game(self, game_id: str) -> Optional[Game]:
        return self.games.get(game_id)

    def get_active_rooms(self) -> List[dict]:
        return [
            {"game_id": game_id, "players": len(game.players)}
            for game_id, game in self.games.items()
            if not game.is_started
        ]


GM = GameManager()
