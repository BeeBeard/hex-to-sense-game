# Модель игры
import pprint
import random
import traceback
import uuid
from typing import List, Union

from fastapi import WebSocket
from loguru import logger
from pyexpat.errors import messages

from app.classes.player import Player
from app.models.models import Hex, SubmitWordResult, GameResponse
from app.worker import word_checker
from app.conn import sql
# Простой словарь для проверки слов


class Game:
    def __init__(
            self,
            creator_id: str,
            room_name: str,
            lives: int,
            max_players: int = 10,
            min_players: int = 1,
            timer: int = 70,
            radius: int = 7):

        self.max_players = max_players                           # Минимальное количество игроков
        self.min_players = min_players                           # Минимальное количество игроков
        self.timer = timer
        self.lives = lives
        self.players: List[Player] = []
        self.used_words = []  # USED_WORDS = set()
        self.current_player_index = 0  # Чей сейчас ход
        self.weights = {
            'Ч': 3, 'Е': 1, 'Л': 2, 'О': 1, 'В': 2, 'К': 2, 'Г': 3, 'Д': 2, 'Р': 2,
            'М': 3, 'Я': 3, 'Н': 2, 'Ь': 3, 'Ж': 3, 'И': 1, 'З': 3, 'А': 1, 'Б': 3,
            'Т': 2, 'У': 3, 'П': 2, 'С': 2, 'Ё': 4, 'Й': 4, 'Ц': 3, 'Щ': 4, 'Ш': 4,
            'Ы': 3, 'Ф': 3, 'Ю': 4, 'Х': 4, 'Ъ': 4, 'Э': 4
        }
        self.room_name = room_name
        self.radius = self.prepare_radius(radius)
        self.center = int((self.radius + 1) / 2) - 1
        self.grid: List[List[Hex]] = []
        self.words = []
        self.generate_grid()
        self.base_words = sql.get_random_rows(20)
        self.fill_grid()
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

            double = False
            for k in neighbors + [self.grid[y][x]]:
                if k.letter == letter:
                    x, y = k.x, k.y
                    # print(f"КООРДИНАТЫ: {x}/{y}")
                    self.grid[y][x].letter = letter
                    double = True
                    break

            if double:
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

    def fill_grid(self):

        words = self.base_words
        words = list(set(words))
        words.sort()
        print(words)
        for word in words:
            self.add_word(word)
            self.get_grid_info(key="letter")

        self.get_grid_info(key="letter")

        _grid = []
        for row in self.grid:
            _row = []
            for i in row:
                if i.show:
                    i.weight = self.weights[i.letter]
                    _row.append(i)
                else:
                    _row.append(None)
            _grid.append(_row)

        self.grid = _grid

    def add_player(self, player_id: str, name: str, websocket: Union[WebSocket, None] = None):

        if len(self.players) < self.max_players and not self.is_started:
            player = Player(player_id=player_id, name=name, lives=self.lives)
            player.websocket = websocket
            self.players.append(player)
            logger.info(f"Player added: id={player_id}, name={name}, game_id={self.game_id}")
            return player_id

        logger.warning(
            f"Failed to add player: game_id={self.game_id}, players_count={len(self.players)}, is_started={self.is_started}")
        return None

    def find_player(self, player_id: str):
        player = next((p for p in self.players if p.player_id == player_id), None)
        if player:
            return player

        return None

    def remove_player(self, player_id: str):

        player = next((p for p in self.players if p.player_id == player_id), None)
        if player:
            self.players.remove(player)
            logger.info(f"Player removed: id={player_id}, name={player.name}, game_id={self.game_id}")
            return player

        return None

    def start_game(self, player_id: str):

        message = (
            f"Ожидание начала игры.\n"
            f"Комната: {self.room_name=}\nИгрок: {player_id=}\nСоздатель: {self.creator_id=}\nКоличество игроков: {len(self.players)}"
        )
        logger.info(message)

        player = next((p for p in self.players if p.player_id == player_id), None)

        if not player:

            error = f"Не удалось запустить игру. Игрок {player_id} не найден для комнаты {self.room_name}"
            message = f"Игрок {player_id} не найден."
            return GameResponse(success=False, message=message, error=error)

        if player_id != self.creator_id:

            error = f"Не удалось запустить игру. Игрок {player_id} не создатель комнаты {self.room_name}"
            message = f"Только создатель может начать игру."
            return GameResponse(success=False, message=message, error=error)


        if len(self.players) < self.min_players:
            error = f"Не удалось запустить игру. Недостаточно игроков для начала. {self.game_id=} | {self.room_name}"
            message = f"Требуется минимум {self.min_players} игрока."
            return GameResponse(success=False, message=message, error=error)

        self.is_started = True
        message = f"Игра успешно создана"
        return GameResponse(success=True, message=message)


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
        if current_player.player_id != player_id:
            error = f"Ход другого игрока.\nТекущий игрок: {current_player.player_id}\nНажавший игрок:{player_id}"
            message = f"Ход другого игрока."
            return GameResponse(success=False, message=message, error=error)

        if 0 <= row < self.radius and 0 <= col < self.radius and self.grid[row][col] is not None:
            self.grid[row][col].clicks += 1
            # logger.info(f"Click incremented: game_id={self.game_id}, player_id={player_id}, row={row}, col={col}, clicks={self.grid[row][col]['clicks']}")
            message = f"Нажатие засчитано"
            return GameResponse(success=True, message=message)

        # logger.warning(f"Invalid cell: game_id={self.game_id}, row={row}, col={col}")
        error = f"Эту ячейку нельзя использовать.\nКомната: {self.room_name}"
        message = f"Эту ячейку нельзя использовать."
        return GameResponse(success=False, message=message, error=error)

    async def submit_word(self, player_id: str, word: str, path: List[List[int]]) -> SubmitWordResult:

        # Обнуляем нажатия
        for r in range(self.radius):
            for c in range(self.radius):
                if self.grid[r][c] is not None:
                    self.grid[r][c].clicks = 0

        word = word.upper()

        for i in self.players:
            pprint.pprint(i.get_data().model_dump())

        current_player = self.players[self.current_player_index]
        # logger.error(f"{player_id=}")
        # logger.error(f"{current_player.get_data()=}")

        if current_player.player_id != player_id or not self.is_started:
            return SubmitWordResult(word=word, valid=False, reason="Не ваша очередь ходить")

        if len(word) < 2:
            current_player.lives -= 1
            return SubmitWordResult(word=word, valid=False, reason="Слово слишком короткое")

        # if not self.is_valid_path(path):
        #     return SubmitWordResult(word=word, valid=False, reason="Invalid path")

        if len(path) != len(word):
            return SubmitWordResult(word=word, valid=False, reason="Длина пути не равна длине слова")

        # Проверяем существует ли слово
        ya_result = word_checker.check_word(word)
        logger.error(f"Данные от яндекс {ya_result}")
        # result = sql.check_update_word(word)
        # result = False

        if not ya_result.is_exist:
            current_player.lives -= 1
            return SubmitWordResult(word=word, valid=False, reason="Такое слово не найдено")

        if word in self.used_words:
            current_player.lives -= 1
            return SubmitWordResult(word=word, valid=False, reason="Слово уже было найдено")

        score = sum(self.grid[r][c].weight for r, c in path)
        current_player.score += score
        current_player.words.append(word)
        self.used_words.append(word)

        return SubmitWordResult(word=word, valid=True, reason="Слово засчитано", score=score)

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
        """Рассылка сообщения"""

        for player in self.players:
            if player.websocket:
                try:
                    await player.websocket.send_json(message)
                    logger.info(f"Broadcast sent to player {player.player_id}, name={player.name}: {message.get('type')}")

                except Exception as e:
                    logger.error(f"Broadcast error to player {player.player_id}: {e} {traceback.format_exc()}")
                    player.websocket = None


if __name__ == "__main__":
    pass
