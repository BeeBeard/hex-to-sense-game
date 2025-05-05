from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import random
import uvicorn
import json
import asyncio
from pydantic import BaseModel
from typing import List, Dict
import uuid
import logging
from config import CONFIG


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Простой словарь для проверки слов
DICTIONARY = {"кот", "дом", "сад", "лес", "мир", "книга", "стол", "окно"}
USED_WORDS = set()

# Модель игрока
class Player:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
        self.score = 0
        self.lives = 5
        self.websocket: WebSocket = None
        self.words: List[str] = []  # Список правильных слов

# Модель игры
class Game:
    def __init__(self, creator_id: str):
        self.players: List[Player] = []
        self.current_player_index = 0
        self.grid = self.generate_grid()
        self.game_id = str(uuid.uuid4())
        self.is_started = False
        self.creator_id = creator_id

    def generate_grid(self):
        letters = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
        row_lengths = [4, 5, 6, 7, 6, 5, 4]
        center_indices = [1.5, 2, 2.5, 3, 2.5, 2, 1.5]
        grid = []
        max_cols = 7
        for i, num_cells in enumerate(row_lengths):
            row = []
            offset = int(3.5 - center_indices[i])
            for j in range(max_cols):
                if offset <= j < offset + num_cells:
                    letter = random.choice(letters)
                    weight = random.randint(1, 5)
                    row.append({"letter": letter, "weight": weight, "clicks": 0})
                else:
                    row.append(None)
            grid.append(row)
        logger.info(f"Generated grid, cell [3][3]: {grid[3][3]}")
        return grid

    def add_player(self, player_id: str, name: str, websocket: WebSocket):
        if len(self.players) < 4 and not self.is_started:
            player = Player(player_id, name)
            player.websocket = websocket
            self.players.append(player)
            logger.info(f"Player added: id={player_id}, name={name}, game_id={self.game_id}")
            return player_id
        logger.warning(f"Failed to add player: game_id={self.game_id}, players_count={len(self.players)}, is_started={self.is_started}")
        return None

    def remove_player(self, player_id: str):
        player = next((p for p in self.players if p.id == player_id), None)
        if player:
            self.players.remove(player)
            logger.info(f"Player removed: id={player_id}, name={player.name}, game_id={self.game_id}")
            return player
        return None

    def start_game(self, player_id: str):
        logger.info(f"Attempting to start game: game_id={self.game_id}, player_id={player_id}, creator_id={self.creator_id}, players_count={len(self.players)}")
        player = next((p for p in self.players if p.id == player_id), None)
        if not player:
            logger.warning(f"Start game failed: player_id={player_id} not found in game {self.game_id}")
            return {"error": f"Player {player_id} not found in game"}
        if player_id != self.creator_id:
            logger.warning(f"Start game failed: player_id={player_id} is not creator_id={self.creator_id}")
            return {"error": f"Only the creator can start the game. Received player_id={player_id}, expected creator_id={self.creator_id}"}
        if len(self.players) < 2:
            logger.warning(f"Start game failed: not enough players in game {self.game_id}")
            return {"error": "At least two players are required"}
        self.is_started = True
        logger.info(f"Game started successfully: game_id={self.game_id}")
        return {"success": True}

    def get_neighbors(self, row: int, col: int):
        neighbors = []
        if row % 2 == 0:
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1)]
        else:
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, 1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            if 0 <= r < 7 and 0 <= c < 7 and self.grid[r][c] is not None:
                neighbors.append((r, c))
        return neighbors

    def is_valid_path(self, path: List[List[int]]):
        if not path:
            return False
        for i in range(1, len(path)):
            prev_r, prev_c = path[i-1]
            curr_r, curr_c = path[i]
            if (curr_r, curr_c) not in self.get_neighbors(prev_r, prev_c):
                return False
        return True

    def increment_click(self, player_id: str, row: int, col: int):
        current_player = self.players[self.current_player_index]
        if current_player.id != player_id:
            logger.warning(f"Invalid click: player_id={player_id} is not current player={current_player.id}")
            return {"valid": False, "reason": "Not your turn"}
        if 0 <= row < 7 and 0 <= col < 7 and self.grid[row][col] is not None:
            self.grid[row][col]["clicks"] += 1
            logger.info(f"Click incremented: game_id={self.game_id}, player_id={player_id}, row={row}, col={col}, clicks={self.grid[row][col]['clicks']}")
            return {"valid": True}
        logger.warning(f"Invalid cell: game_id={self.game_id}, row={row}, col={col}")
        return {"valid": False, "reason": "Invalid cell"}

    def submit_word(self, player_id: str, word: str, path: List[List[int]]):
        global USED_WORDS
        current_player = self.players[self.current_player_index]
        if current_player.id != player_id:
            logger.warning(f"Invalid word submission: player_id={player_id} is not current player={current_player.id}")
            return {"valid": False, "reason": "Not your turn", "word": word}
        if not self.is_valid_path(path):
            current_player.lives -= 1
            logger.info(f"Invalid path for word: {word}, player_id={player_id}, lives={current_player.lives}")
            return {"valid": False, "reason": "Invalid path", "word": word}
        if word.lower() not in DICTIONARY:
            current_player.lives -= 1
            logger.info(f"Word not in dictionary: {word}, player_id={player_id}, lives={current_player.lives}")
            return {"valid": False, "reason": "Word not in dictionary", "word": word}
        if word.lower() in USED_WORDS:
            current_player.lives -= 1
            logger.info(f"Word already used: {word}, player_id={player_id}, lives={current_player.lives}")
            return {"valid": False, "reason": "Word already used", "word": word}
        score = sum(self.grid[r][c]["weight"] for r, c in path)
        current_player.score += score
        current_player.words.append(word.lower())
        USED_WORDS.add(word.lower())
        for r in range(7):
            for c in range(7):
                if self.grid[r][c] is not None:
                    self.grid[r][c]["clicks"] = 0
        logger.info(f"Word accepted: {word}, score={score}, player_id={player_id}")
        return {"valid": True, "score": score, "word": word}

    def next_turn(self):
        if not self.players:
            return None
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        while self.players and self.players[self.current_player_index].lives <= 0:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
        logger.info(f"Next turn: game_id={self.game_id}, current_player_index={self.current_player_index}")
        return self.current_player_index

    def is_game_over(self):
        return len(self.players) <= 1 or sum(1 for p in self.players if p.lives > 0) <= 1

    async def broadcast(self, message: dict):
        for player in self.players:
            if player.websocket:
                try:
                    await player.websocket.send_json(message)
                    logger.info(f"Broadcast sent to player {player.id}, name={player.name}: {message.get('type')}")
                except Exception as e:
                    logger.error(f"Broadcast error to player {player.id}: {e}")
                    player.websocket = None

# Хранилище игр
games: Dict[str, Game] = {}

@app.get("/", response_class=HTMLResponse)
async def get():
    logger.info("Received GET request for /")
    try:
        with open("static/index.html", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        logger.error(f"Error reading index.html: {e}")
        return HTMLResponse(content="Error loading page", status_code=500)

@app.get("/join/{game_id}", response_class=HTMLResponse)
async def join_game_page(game_id: str):
    logger.info(f"Received GET request for /join/{game_id}")
    try:
        with open("static/index.html", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        logger.error(f"Error reading index.html: {e}")
        return HTMLResponse(content="Error loading page", status_code=500)

@app.websocket("/ws/{game_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str, player_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connected: game_id={game_id}, player_id={player_id}")
    game = games.get(game_id)
    if not game:
        logger.error(f"WebSocket error: Game {game_id} not found")
        await websocket.send_json({"type": "error", "message": "Game not found"})
        await websocket.close()
        return

    player = next((p for p in game.players if p.id == player_id), None)
    if not player:
        logger.error(f"WebSocket error: Player {player_id} not found in game {game_id}")
        await websocket.send_json({"type": "error", "message": f"Player {player_id} not found"})
        await websocket.close()
        return

    player.websocket = websocket
    try:
        await game.broadcast({
            "type": "init",
            "grid": game.grid,
            "players": [{"id": p.id, "name": p.name, "score": p.score, "lives": p.lives, "words": p.words} for p in game.players],
            "current_player": game.players[game.current_player_index].id if game.is_started and game.players else None,
            "current_player_name": game.players[game.current_player_index].name if game.is_started and game.players else None,
            "is_started": game.is_started
        })
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            logger.info(f"Received WebSocket action: {action}, from player_id={player_id}, game_id={game_id}")
            if action == "start_game":
                received_player_id = data.get("player_id", player_id)
                logger.info(f"Processing start_game: received_player_id={received_player_id}, websocket_player_id={player_id}")
                result = game.start_game(received_player_id)
                if result.get("error"):
                    logger.warning(f"Start game failed: {result['error']}")
                    await websocket.send_json({"type": "error", "message": result["error"]})
                else:
                    game.is_started = True
                    logger.info(f"Game started successfully: game_id={game_id}")
                    await game.broadcast({
                        "type": "start",
                        "grid": game.grid,
                        "players": [{"id": p.id, "name": p.name, "score": p.score, "lives": p.lives, "words": p.words} for p in game.players],
                        "current_player": game.players[game.current_player_index].id if game.players else None,
                        "current_player_name": game.players[game.current_player_index].name if game.is_started and game.players else None,
                        "is_started": True,
                        "message": "Игра началась!"
                    })
            elif action == "submit_word":
                word = data.get("word")
                path = data.get("path")
                result = game.submit_word(player_id, word, path)
                game.next_turn()
                await game.broadcast({
                    "type": "update",
                    "result": result,
                    "grid": game.grid,
                    "players": [{"id": p.id, "name": p.name, "score": p.score, "lives": p.lives, "words": p.words} for p in game.players],
                    "current_player": game.players[game.current_player_index].id if game.players else None,
                    "current_player_name": game.players[game.current_player_index].name if game.is_started and game.players else None,
                    "is_started": True,
                    "message": f"Ход игрока {game.players[game.current_player_index].name}" if game.players else "Игра продолжается"
                })
            elif action == "increment_click":
                row = data.get("row")
                col = data.get("col")
                result = game.increment_click(player_id, row, col)
                if result["valid"]:
                    await game.broadcast({
                        "type": "click_update",
                        "grid": game.grid,
                        "row": row,
                        "col": col,
                        "clicks": game.grid[row][col]["clicks"]
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": result["reason"]
                    })
            elif action == "timeout":
                if game.players and game.players[game.current_player_index].id == player_id:
                    game.players[game.current_player_index].lives -= 1
                    game.next_turn()
                    await game.broadcast({
                        "type": "update",
                        "result": {"valid": False, "reason": "Time out"},
                        "grid": game.grid,
                        "players": [{"id": p.id, "name": p.name, "score": p.score, "lives": p.lives, "words": p.words} for p in game.players],
                        "current_player": game.players[game.current_player_index].id if game.players else None,
                        "current_player_name": game.players[game.current_player_index].name if game.is_started and game.players else None,
                        "is_started": True,
                        "message": f"Ход игрока {game.players[game.current_player_index].name}" if game.players else "Игра продолжается"
                    })
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: player_id={player_id}, game_id={game_id}")
        disconnected_player = game.remove_player(player_id)
        if disconnected_player:
            message = f"Игрок {disconnected_player.name} покинул игру"
            if not game.players:
                logger.info(f"No players left in game {game_id}, removing game")
                del games[game_id]
                return
            if game.is_started and game.players and game.current_player_index < len(game.players) and game.players[game.current_player_index].id == player_id:
                game.next_turn()
                await game.broadcast({
                    "type": "update",
                    "grid": game.grid,
                    "players": [{"id": p.id, "name": p.name, "score": p.score, "lives": p.lives, "words": p.words} for p in game.players],
                    "current_player": game.players[game.current_player_index].id if game.players else None,
                    "current_player_name": game.players[game.current_player_index].name if game.is_started and game.players else None,
                    "is_started": True,
                    "message": f"{message}. Ход игрока {game.players[game.current_player_index].name}" if game.players else message
                })
            else:
                await game.broadcast({
                    "type": "info",
                    "message": message,
                    "players": [{"id": p.id, "name": p.name, "score": p.score, "lives": p.lives, "words": p.words} for p in game.players]
                })
            if len(game.players) == 1 and game.is_started:
                await game.broadcast({
                    "type": "info",
                    "message": "Вы остались один. Продолжить игру?",
                    "players": [{"id": p.id, "name": p.name, "score": p.score, "lives": p.lives, "words": p.words} for p in game.players]
                })
    except Exception as e:
        logger.error(f"WebSocket error: game_id={game_id}, player_id={player_id}, error={e}")
        await websocket.send_json({"type": "error", "message": f"Server error: {str(e)}"})
        await websocket.close()

class CreateGameRequest(BaseModel):
    player_name: str

class JoinGameRequest(BaseModel):
    game_id: str
    player_name: str

@app.post("/create_game")
async def create_game(request: CreateGameRequest):
    player_name = request.player_name.strip() or f"Игрок_{random.randint(1000, 9999)}"
    logger.info(f"Processing create_game request for player: {player_name}")
    player_id = str(uuid.uuid4())
    game = Game(creator_id=player_id)
    game.add_player(player_id, player_name, None)
    games[game.game_id] = game
    logger.info(f"Game created: game_id={game.game_id}, player_id={player_id}, creator_id={player_id}, player_name={player_name}")
    return {"game_id": game.game_id, "player_id": player_id, "creator_id": player_id}

@app.post("/join_game")
async def join_game(request: JoinGameRequest):
    player_name = request.player_name.strip() or f"Игрок_{random.randint(1000, 9999)}"
    logger.info(f"Processing join_game request: game_id={request.game_id}, player_name={player_name}")
    game = games.get(request.game_id.strip())
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


def main():

    print()

    try:

        logger.info(f"Подключение и настройка базы данных")

        logger.info(f"Запуск APP: http://{CONFIG.api.full_path}")
        logger.info(f"Swagger: http://{CONFIG.api.docs}")
        uvicorn.run(
            app=app,
            host=CONFIG.api.ip,
            port=CONFIG.api.port,
            log_level="debug",
            # reload=True
        )

    except KeyboardInterrupt:
        logger.info(f"Сервер остановлен")
    except Exception as e:
        logger.exception(e)
    finally:
        logger.info(f"Выключение APP")


if __name__ == "__main__":
    main()
