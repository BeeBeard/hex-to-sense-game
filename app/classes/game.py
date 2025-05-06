# Модель игры

import random
import uuid
from typing import List, Union

from fastapi import WebSocket
from loguru import logger
from app.classes.player import Player

# Простой словарь для проверки слов

DICTIONARY = {"кот", "дом", "сад", "лес", "мир", "книга", "стол", "окно"}
USED_WORDS = set()


class Game:
    def __init__(self, creator_id: str, radius: int = 7):
        self.players: List[Player] = []
        self.current_player_index = 0
        self.radius = self.prepare_radius(radius)
        self.grid = self.generate_grid()
        self.game_id = str(uuid.uuid4())
        self.is_started = False
        self.creator_id = creator_id

    @staticmethod
    def prepare_radius(radius: int):
        _r = radius
        if not _r % 2:
            _r = radius + 1

        if _r > 9:
            _r = 9

        if _r < 5:
            _r = 5
        print(f"{_r=}")
        return _r


    def generate_grid(self):

        letters = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"

        center = int((self.radius + 1) / 2)
        # shift = self.radius // 2 + 1
        # row_lengths = [self.radius - abs((i + 1) - shift) for i in range(self.radius)]
        # center_indices = [shift - 1 - abs((i + 1) - shift) * 0.5 for i in range(self.radius)]

        # mapping = []
        # for i in range(self.radius):
        #     row = [1 if k < row_lengths[i] else 0 for k in range(self.radius)]
        #     n = row_lengths[i] + 1
        #     mapping.append(row[n:] + row[:n]) if n >= 0 else mapping.append(row)

        mapping = [
            [0, 1, 1, 1, 0],
            [1, 1, 1, 1, 0],
            [1, 1, 1, 1, 1],
            [1, 1, 1, 1, 0],
            [0, 1, 1, 1, 0],

        ]

        if self.radius == 7:
            mapping = [
                [0, 0, 1, 1, 1, 1, 0],
                [0, 1, 1, 1, 1, 1, 0],
                [0, 1, 1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1, 1, 1],
                [0, 1, 1, 1, 1, 1, 1],
                [0, 1, 1, 1, 1, 1, 0],
                [0, 0, 1, 1, 1, 1, 0],
            ]

        if self.radius == 9:
            mapping = [
                [0, 0, 1, 1, 1, 1, 1, 0, 0],
                [0, 1, 1, 1, 1, 1, 1, 0, 0],
                [0, 1, 1, 1, 1, 1, 1, 1, 0],
                [1, 1, 1, 1, 1, 1, 1, 1, 0],
                [1, 1, 1, 1, 1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1, 1, 1, 1, 0],
                [0, 1, 1, 1, 1, 1, 1, 1, 0],
                [0, 1, 1, 1, 1, 1, 1, 0, 0],
                [0, 0, 1, 1, 1, 1, 1, 0, 0],
            ]

        grid = []
        for row in mapping:

            new_row = []
            for k in row:
                if k:
                    letter = random.choice(letters)
                    weight = random.randint(1, 5)
                    new_row.append({"letter": f"{row[k]} {k}", "weight": weight, "clicks": 0})
                    # row.append({"letter": letter, "weight": weight, "clicks": 0})
                else:
                    new_row.append(None)

            grid.append(new_row)

        logger.info(f"Generated grid, cell [{center}][{center}]: {grid[center][center]}")
        return grid

    def add_player(self, player_id: str, name: str, websocket: Union[WebSocket, None]):
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
            if 0 <= r < self.radius and 0 <= c < self.radius and self.grid[r][c] is not None:
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
        if 0 <= row < self.radius and 0 <= col < self.radius and self.grid[row][col] is not None:
            self.grid[row][col]["clicks"] += 1
            logger.info(f"Click incremented: game_id={self.game_id}, player_id={player_id}, row={row}, col={col}, clicks={self.grid[row][col]['clicks']}")
            return {"valid": True}
        logger.warning(f"Invalid cell: game_id={self.game_id}, row={row}, col={col}")
        return {"valid": False, "reason": "Invalid cell"}

    def submit_word(self, player_id: str, word: str, path: List[List[int]]):
        # global USED_WORDS
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
        for r in range(self.radius):
            for c in range(self.radius):
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






if __name__ == "__main__":
    pass
