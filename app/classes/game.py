# Модель игры
import pprint
import random
import uuid
from typing import List, Union

from fastapi import WebSocket
from loguru import logger
from app.classes.player import Player
from app.classes import word_checker
from app.models.game import Hex, SubmitWordResult
from typing import List, Optional

# Простой словарь для проверки слов

USED_WORDS = set()


class Game:
    def __init__(self, creator_id: str, radius: int = 7):
        self.players: List[Player] = []
        self.current_player_index = 0
        self.weights = {
            'Ч': 3, 'Е': 1, 'Л': 2, 'О': 1, 'В': 2, 'К': 2, 'Г': 3, 'Д': 2, 'Р': 2,
            'М': 3, 'Я': 3, 'Н': 2, 'Ь': 3, 'Ж': 3, 'И': 1, 'З': 3, 'А': 1, 'Б': 3,
            'Т': 2, 'У': 3, 'П': 2, 'С': 2, 'Ё': 4, 'Й': 4, 'Ц': 3, 'Щ': 4, 'Ш': 4,
            'Ы': 3, 'Ф': 3, 'Ю': 4, 'Х': 4, 'Ъ': 4, 'Э': 4
        }

        self.radius = self.prepare_radius(radius)
        self.center = int((self.radius + 1) / 2) - 1
        self.grid = []
        self.words = []
        # self.letters = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЧЦШЩЪЫЬЭЮЯ"
        self.generate_grid()

        self.fill_grid(["ГАЗООБРАЗОВАНИЕ", "ГАЗООБРАЗОВАНИЕ", "МЕНЕДЖЕР", "ПРИЮТ", "БЕТОН", "КОЛЛЕГА", "КОТ", "НУГА", "ПРАВИЛО", "ТРАВА"])
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
        # print(f"{_r=}")
        return _r

    def generate_grid(self):

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

        c = 0
        for y, row in enumerate(mapping):

            new_row = []
            for x, k in enumerate(row):
                _hex = Hex(number=c, x=x, y=y)
                if not k:
                    _hex.show = False
                new_row.append(_hex)
                c += 1

            self.grid.append(new_row)

        # logger.info(f"Generated grid, cell [{center}][{center}]: {grid[center][center].number}")
        return self.grid

    @staticmethod
    def get_keys_from_hex_list(row: List[Hex], key: str):
        return [k.model_dump().get(key) for k in row]

    def get_grid_info(self, key: str = "number"):
        _grid = []
        for y, row in enumerate(self.grid):
            # _row = [k.model_dump().get(key) for k in row]
            _row = self.get_keys_from_hex_list(row, key)
            _grid.append(_row)
            if y % 2:
                print("  ", _row)
            else:
                print(_row)

        return _grid

    def get_neighbors(self, x: int, y: int):

        if y % 2 == 0:
            directions = [(0, -1), (1, 0),  (0, 1),  (1, -1), (-1, -1), (-1, 0),]
        else:
            directions = [(-1, 1), (1, 0), (1, 1),  (0, 1), (-1, 0), (0, -1), ]

        neighbors: List[Hex] = []
        for dr, dc in directions:
            _x, _y = x + dr, y + dc
            if 0 <= _x < self.radius and 0 <= _y < self.radius:
                neighbors.append(self.grid[_y][_x])

        # print(f"СОСЕДИ: {x}/{y}")
        #
        # # self.get_grid_info("letter")
        # # print()
        #
        # _grid = []
        # for row in range(self.radius):
        #     _row = []
        #     for k in range(self.radius):
        #         _row.append(" ")
        #     _grid.append(_row)
        #
        # for i, v in enumerate(neighbors):
        #     # print(f"{_grid[i.x][i.y]=}")
        #     _grid[v.y][v.x] = i
        # _grid[y][x] = "X"
        #
        # for i, row in enumerate(_grid):
        #     if i % 2:
        #         print("  ", row)
        #     else:
        #         print(row)
        #
        # print(f"END")

        return neighbors

    def get_empty_neighbors(self, x: int, y: int):
        neighbors = self.get_neighbors(x, y)
        return [i for i in neighbors if i.letter == " " and i.show]

    def find_free_hex(self, count: int = 6):

        # Ищем сначала самые свободные ячейки от 6 затем меньше
        for _m in reversed(range(0, count + 1)):

            for y, row in enumerate(self.grid):
                for x, k in enumerate(row):
                    if k.letter == " " and k.show:
                        neighbors = self.get_empty_neighbors(k.x, k.y)
                        if len(neighbors) == _m or _m == 0:
                            return x, y

        return False

    def add_word(self, word: str):
        """
        word - несколько слов подряд
        при "-" ищем место где свободны 6 соседей
        """

        self.words.append(word)
        print(word)

        # Выбор начальной точки
        free_hex = self.find_free_hex()

        if not free_hex:
            return

        x, y = free_hex[0], free_hex[1]
        # print(f"КООРДИНАТЫ для слова {word}: {x}/{y}")

        for i, letter in enumerate(word):

            if i == 0:
                self.grid[y][x].letter = letter
                continue

            neighbors = self.get_empty_neighbors(x, y)
            # if not neighbors:
            #     self.words = self.words[:-1]
            #     return

            duble = False
            for k in neighbors + [self.grid[y][x]]:
                if k.letter == letter:
                    x, y = k.x, k.y
                    # print(f"КООРДИНАТЫ: {x}/{y}")
                    self.grid[y][x].letter = letter
                    duble = True
                    break

            if duble:
                continue

            neighbors = self.get_empty_neighbors(x, y)
            if neighbors:

                # Что бы выбирать случайное направление
                # cur_neighbors = empty_neighbors[random.randint(0, len(empty_neighbors) - 1)]
                # if not len(empty_neighbors) - 1 > next_index:
                #     next_index = 0
                next_index = 0

                cur_neighbors = neighbors[next_index]

                x, y = cur_neighbors.x, cur_neighbors.y
                # print(f"КООРДИНАТЫ: {x}/{y}")
                self.grid[y][x].letter = letter
            else:
                # self.words = self.words[:-1]
                return

        # print(self.words)

    def fill_grid(self, words: List[str]):

        words = list(set(words))
        words.sort()
        print(words)
        for word in words:
            self.add_word(word)
            self.get_grid_info(key="letter")

        print("RESULT")
        self.get_grid_info(key="letter")

        _grid = []
        for row in self.grid:
            _row = []
            for i in row:
                if i.show:
                    # i.letter = f"{i.number}"
                    i.weight = self.weights[i.letter]
                    _row.append(i.model_dump())
                else:
                    _row.append(None)
            # _row = [i.model_dump() for i in row]
            # print(_row)
            _r = [i["letter"] for i in _row if i]
            print(_r)
            _grid.append(_row)

        self.grid = _grid

    def add_player(self, player_id: str, name: str, websocket: Union[WebSocket, None] = None):

        if len(self.players) < 4 and not self.is_started:
            player = Player(player_id, name)
            player.websocket = websocket
            self.players.append(player)
            logger.info(f"Player added: id={player_id}, name={name}, game_id={self.game_id}")
            return player_id

        logger.warning(
            f"Failed to add player: game_id={self.game_id}, players_count={len(self.players)}, is_started={self.is_started}")
        return None

    def remove_player(self, player_id: str):

        player = next((p for p in self.players if p.id == player_id), None)
        if player:
            self.players.remove(player)
            logger.info(f"Player removed: id={player_id}, name={player.name}, game_id={self.game_id}")
            return player

        return None

    def start_game(self, player_id: str):

        logger.info(
            f"Attempting to start game: game_id={self.game_id}, player_id={player_id}, creator_id={self.creator_id}, players_count={len(self.players)}")
        player = next((p for p in self.players if p.id == player_id), None)

        if not player:
            logger.warning(f"Start game failed: player_id={player_id} not found in game {self.game_id}")
            return {"error": f"Player {player_id} not found in game"}

        if player_id != self.creator_id:
            logger.warning(f"Start game failed: player_id={player_id} is not creator_id={self.creator_id}")
            return {
                "error": f"Only the creator can start the game. Received player_id={player_id}, expected creator_id={self.creator_id}"}

        if len(self.players) < 2:
            logger.warning(f"Start game failed: not enough players in game {self.game_id}")
            return {"error": "At least two players are required"}

        self.is_started = True
        logger.info(f"Game started successfully: game_id={self.game_id}")
        return {"success": True}

    def is_valid_path(self, path: List[List[int]]):
        if not path:
            return False

        for i in range(1, len(path)):
            prev_r, prev_c = path[i - 1]
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
            logger.info(
                f"Click incremented: game_id={self.game_id}, player_id={player_id}, row={row}, col={col}, clicks={self.grid[row][col]['clicks']}")
            return {"valid": True}

        logger.warning(f"Invalid cell: game_id={self.game_id}, row={row}, col={col}")
        return {"valid": False, "reason": "Invalid cell"}

    def submit_word(self, player_id: str, word: str, path: List[List[int]]):

        word = word.upper()

        for i in self.players:
            pprint.pprint(i.get_data())

        current_player = self.players[self.current_player_index]

        logger.error(f"{player_id=}")
        logger.error(f"{current_player.get_data()=}")
        if current_player.id != player_id or not self.is_started:

            return SubmitWordResult(word=word, valid=False, reason="Not your turn or game not started").model_dump()

        if len(word) < 2:
            return SubmitWordResult(word=word, valid=False, reason="Word too short").model_dump()

        logger.error(f"ПРОВЕРИТЬ!!! {path=}")
        # if not self.is_valid_path(path):
        #     return SubmitWordResult(word=word, valid=False, reason="Invalid path").model_dump()

        if len(path) != len(word):
            return SubmitWordResult(word=word, valid=False, reason="Path length does not match word length").model_dump()


        # Проверяем существует ли слово
        is_exist = word_checker.check_word(word).is_exist

        if word is is_exist:
            current_player.lives -= 1
            return SubmitWordResult(word=word, valid=False, reason="Такое слово не найдено").model_dump()

        if word in USED_WORDS:
            return SubmitWordResult(word=word, valid=False, reason="Word already used").model_dump()

        score = sum(self.grid[r][c]["weight"] for r, c in path)
        current_player.score += score
        logger.debug(f"CHECK!! {current_player.score=}")
        current_player.words.append(word)
        USED_WORDS.add(word)

        for r in range(self.radius):
            for c in range(self.radius):
                if self.grid[r][c] is not None:
                    self.grid[r][c]["clics"] = 0

        return SubmitWordResult(word=word, valid=True, reason="Word accepted", score=score).model_dump()

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
