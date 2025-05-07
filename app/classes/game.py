# Модель игры

import random
import uuid
from typing import List, Union

from fastapi import WebSocket
from loguru import logger
from app.classes.player import Player
from app.classes import word_checker
import random
from typing import List, Dict, Set, Tuple
import logging


# Простой словарь для проверки слов

DICTIONARY = {"кот", "дом", "сад", "лес", "мир", "книга", "стол", "окно"}
USED_WORDS = set()

bigram_prob = {'че': 58, 'ел': 130, 'ло': 115, 'ов': 128, 'ве': 105, 'ек': 61, 'го': 54, 'од': 124, 'вр': 16, 'ре': 187,
               'ем': 39, 'мя': 8, 'де': 111, 'ен': 334, 'нь': 29, 'жи': 26, 'из': 58, 'зн': 21, 'ра': 253, 'аз': 64,
               'аб': 34, 'бо': 65, 'от': 123, 'та': 141, 'ру': 63, 'ук': 37, 'ка': 297, 'ор': 172, 'ро': 203, 'во': 163,
               'оп': 44, 'пр': 175, 'ос': 218, 'сл': 40, 'ме': 98, 'ес': 104, 'ст': 426, 'то': 130, 'еб': 16, 'бё': 1,
               'ён': 4, 'но': 155, 'ок': 100, 'др': 23, 'уг': 15, 'сс': 44, 'си': 46, 'ия': 149, 'ми': 45, 'ир': 30,
               'лу': 24, 'уч': 26, 'ча': 47, 'ай': 22, 'он': 108, 'на': 152, 'гл': 12, 'ла': 81, 'до': 73, 'ом': 66,
               'тр': 118, 'ан': 202, 'ли': 91, 'иц': 39, 'цо': 3, 'ил': 38, 'же': 45, 'нщ': 1, 'щи': 14, 'ин': 147,
               'ас': 84, 'ть': 130, 'ис': 81, 'те': 157, 'ма': 85, 'ви': 79, 'ид': 30, 'ол': 138, 'ва': 90, 'ко': 147,
               'не': 90, 'ец': 32, 'об': 82, 'бл': 36, 'ле': 132, 'тн': 22, 'ош': 11, 'ше': 22, 'ни': 396, 'ие': 340,
               'бр': 28, 'мо': 80, 'ск': 48, 'кв': 9, 'ьг': 1, 'ги': 22, 'зе': 13, 'мл': 6, 'ля': 16, 'кн': 9, 'иг': 18,
               'га': 31, 'мп': 25, 'па': 69, 'ри': 118, 'оз': 37, 'зм': 22, 'ож': 37, 'жн': 12, 'ез': 29, 'зу': 5,
               'ул': 30, 'ль': 147, 'ьт': 9, 'ат': 117, 'аш': 11, 'ши': 10, 'гр': 43, 'уп': 34, 'пп': 7, 'ав': 70,
               'ой': 16, 'йн': 9, 'пу': 25, 'ут': 21, 'им': 39, 'тв': 106, 'ет': 97, 'ог': 52, 'да': 90, 'яз': 7,
               'зы': 5, 'ык': 7, 'еш': 10, 'ар': 105, 'вл': 31, 'оч': 34, 'чь': 6, 'дв': 12, 'ер': 180, 'рь': 21,
               'ур': 37, 'за': 96, 'ак': 62, 'зв': 22, 'ит': 88, 'ти': 99, 'ам': 49, 'мм': 12, 'ач': 15, 'ал': 94,
               'нт': 74, 'по': 188, 'ощ': 10, 'щь': 3, 'це': 31, 'чи': 26, 'ты': 12, 'ыс': 11, 'ся': 7, 'яч': 3,
               'ну': 7, 'нф': 7, 'фо': 22, 'рм': 20, 'ац': 37, 'ци': 94, 'оц': 10, 'вт': 11, 'яц': 3, 'мы': 9, 'св': 18,
               'шк': 19, 'ей': 24, 'йс': 17, 'ту': 48, 'уа': 5, 'вн': 22, 'вз': 7, 'зг': 4, 'яд': 9, 'ус': 41, 'му': 23,
               'уж': 19, 'жч': 1, 'лю': 25, 'юб': 7, 'вь': 8, 'вя': 3, 'зь': 4, 'рг': 13, 'ья': 9, 'ср': 7, 'ед': 87,
               'дс': 12, 'ду': 21, 'уш': 14, 'ша': 17, 'пи': 38, 'сь': 9, 'ьм': 6, 'бщ': 6, 'ще': 36, 'со': 79,
               'оя': 11, 'ян': 13, 'еч': 27, 'см': 21, 'се': 45, 'мь': 3, 'су': 32, 'уд': 35, 'рс': 17, 'ещ': 8,
               'ев': 37, 'ву': 4, 'ич': 23, 'ое': 21, 'кт': 49, 'ца': 27, 'ры': 18, 'ын': 7, 'чк': 23, 'мн': 7,
               'сы': 12, 'ея': 7, 'ят': 28, 'ьн': 23, 'иж': 8, 'чу': 3, 'ув': 8, 'вс': 7, 'рт': 42, 'ад': 55, 'ря': 14,
               'пл': 49, 'ип': 10, 'пы': 6, 'ыт': 12, 'рд': 6, 'дц': 2, 'ау': 3, 'оо': 12, 'нн': 32, 'ны': 7, 'ые': 4,
               'иа': 18, 'бы': 9, 'ьш': 3, 'нс': 36, 'ьс': 14, 'зи': 25, 'уб': 24, 'фи': 27, 'би': 29, 'лл': 16,
               'ио': 25, 'ку': 33, 'кс': 21, 'ум': 21, 'чл': 1, 'еф': 5, 'сп': 61, 'сч': 4, 'чё': 8, 'ёт': 12, 'ди': 57,
               'нц': 18, 'са': 33, 'йт': 3, 'зо': 22, 'пе': 81, 'дь': 14, 'ик': 127, 'кл': 37, 'ои': 12, 'йо': 2,
               'сн': 15, 'фа': 14, 'зд': 30, 'ап': 31, 'дп': 5, 'аг': 27, 'хо': 33, 'нд': 25, 'ьч': 2, 'жб': 2,
               'ба': 43, 'ух': 9, 'кр': 44, 'зр': 15, 'ьз': 3, 'бъ': 6, 'ъе': 7, 'ьб': 5, 'дм': 3, 'чо': 4, 'уз': 11,
               'лё': 9, 'ха': 12, 'ге': 16, 'лн': 10, 'жу': 3, 'рн': 15, 'рр': 5, 'ня': 17, 'еп': 21, 'ех': 9, 'дл': 4,
               'аж': 25, 'жд': 25, 'ищ': 7, 'чн': 7, 'вы': 30, 'ыб': 4, 'нк': 25, 'пь': 3, 'ью': 2, 'ют': 2, 'хн': 4,
               'ых': 4, 'бе': 33, 'ег': 15, 'дн': 19, 'иб': 10, 'бк': 6, 'рк': 18, 'бу': 19, 'ущ': 9, 'ее': 6, 'дд': 3,
               'рж': 11, 'жк': 10, 'ащ': 10, 'ье': 12, 'ео': 5, 'сш': 4, 'ах': 8, 'эк': 15, 'зя': 5, 'яи': 1, 'лд': 2,
               'еж': 21, 'цв': 2, 'тк': 28, 'ий': 12, 'тс': 13, 'бх': 1, 'бя': 3, 'ыв': 11, 'эн': 5, 'бн': 6, 'щу': 1,
               'ив': 32, 'сф': 2, 'фе': 20, 'ун': 14, 'фу': 4, 'кц': 14, 'вп': 2, 'тл': 2, 'жа': 25, 'ъё': 2, 'ём': 5,
               'ки': 17, 'эл': 5, 'нв': 6, 'вг': 1, 'гу': 8, 'сц': 4, 'дг': 1, 'вк': 26, 'тя': 5, 'яб': 4, 'мк': 4,
               'еа': 8, 'рф': 3, 'фр': 9, 'ыр': 7, 'иё': 2, 'бс': 8, 'ию': 2, 'юн': 3, 'ща': 6, 'дх': 1, 'оэ': 5,
               'эт': 3, 'оф': 17, 'юц': 2, 'яв': 7, 'тд': 4, 'ху': 3, 'юл': 3, 'аф': 10, 'ох': 13, 'ёр': 11, 'шл': 4,
               'аи': 4, 'лп': 1, 'пт': 6, 'яй': 3, 'ая': 11, 'ыл': 9, 'лк': 16, 'лы': 4, 'хл': 2, 'бю': 3, 'юд': 6,
               'дж': 7, 'лг': 3, 'хр': 12, 'эф': 4, 'фф': 3, 'нё': 2, 'юч': 8, 'сх': 6, 'хе': 1, 'их': 9, 'хи': 8,
               'шт': 7, 'фл': 4, 'эп': 2, 'ып': 4, 'рп': 7, 'вх': 1, 'дк': 13, 'ыш': 11, 'рч': 2, 'рх': 5, 'хм': 3,
               'дя': 2, 'гн': 7, 'чр': 1, 'ящ': 3, 'зк': 3, 'шу': 2, 'чт': 4, 'иф': 7, 'пц': 3, 'иш': 4, 'лж': 3,
               'ке': 8, 'щн': 3, 'йл': 3, 'ды': 10, 'рв': 6, 'пк': 6, 'сю': 2, 'юж': 1, 'тч': 7, 'дё': 1, 'ёж': 3,
               'жь': 4, 'нч': 1, 'мв': 2, 'тю': 4, 'юр': 5, 'яс': 4, 'еи': 2, 'ъя': 2, 'зл': 4, 'юм': 3, 'юг': 1,
               'бм': 2, 'фт': 2, 'бб': 1, 'пя': 6, 'яж': 5, 'ьц': 1, 'рш': 3, 'ыч': 3, 'эм': 2, 'тё': 9, 'хв': 1,
               'кз': 5, 'нг': 8, 'тм': 4, 'нж': 1, 'мс': 2, 'рб': 3, 'сд': 5, 'сё': 3, 'мг': 1, 'ым': 2, 'йм': 1,
               'сб': 5, 'шо': 6, 'эз': 1, 'пс': 3, 'ьё': 4, 'ёд': 2, 'кд': 1, 'шр': 1, 'тп': 2, 'вв': 2, 'рл': 2,
               'йц': 3, 'мб': 3, 'шн': 2, 'йк': 8, 'вч': 1, 'лч': 3, 'уц': 1, 'цу': 1, 'ыз': 1, 'ёл': 4, 'дъ': 2,
               'чв': 1, 'нр': 1, 'лм': 1, 'бв': 1, 'бз': 2, 'нз': 3, 'чш': 1, 'аэ': 2, 'эр': 3, 'тф': 1, 'эв': 1,
               'съ': 1, 'яр': 3, 'еу': 3, 'пн': 2, 'зч': 1, 'шь': 2, 'рё': 3, 'ёв': 1, 'ял': 1, 'шц': 1, 'ёб': 1,
               'дт': 1, 'тз': 2, 'юз': 3, 'ыг': 1, 'мэ': 1, 'дб': 2, 'оу': 5, 'гм': 1, 'эх': 1, 'дч': 1, 'ае': 2,
               'тб': 4, 'ям': 1, 'вё': 3, 'зб': 2, 'уй': 1, 'тт': 2, 'тъ': 1, 'яп': 2, 'гч': 1, 'вщ': 2, 'ню': 1,
               'як': 4, 'рю': 4, 'юк': 2, 'вм': 2, 'ьк': 1, 'аю': 2, 'ющ': 3, 'йз': 1, 'юс': 4, 'шм': 1, 'ыд': 3,
               'ыж': 3, 'жо': 2, 'ый': 4, 'ёк': 3, 'фё': 1, 'шё': 1, 'мё': 2, 'рц': 1, 'жм': 1, 'ёг': 1, 'гк': 1,
               'зё': 1, 'гв': 2, 'лб': 2, 'рз': 1, 'лс': 1, 'уя': 2, 'мр': 1, 'уи': 1, 'вц': 1, 'вд': 2, 'оа': 1,
               'кп': 1, 'лщ': 1, 'ую': 1, 'ёс': 2, 'мф': 1, 'ьв': 1, 'ьп': 2, 'пм': 1, 'ёщ': 1, 'яг': 1, 'кк': 1,
               'йд': 1, 'въ': 1, 'йб': 2, 'уо': 1, 'тх': 1, 'иу': 1, 'уф': 1, 'шю': 1, 'лф': 1, 'ьщ': 1, 'ьф': 1,
               'фч': 1, 'нх': 1, 'шв': 1, 'аё': 1, 'ии': 1, 'тг': 1}

letter_prob = {'ч': 0.01079761258817146, 'е': 0.09169831795984808, 'л': 0.04096581660336408, 'о': 0.09424850786760716,
               'в': 0.03472599023331525, 'к': 0.04823657080846446, 'г': 0.013022246337493217, 'д': 0.030548019533369507,
               'р': 0.06462289744981009, 'м': 0.025339120998372218, 'я': 0.015735214324470972, 'н': 0.06326641345632121,
               'ь': 0.020781334780249593, 'ж': 0.009278350515463918, 'и': 0.0742810634834509, 'з': 0.017362995116657624,
               'а': 0.09316332067281606, 'б': 0.017362995116657624, 'т': 0.06776994031470429, 'у': 0.022734671730873575,
               'п': 0.03678784590341834, 'с': 0.05653825284861639, 'ё': 0.002930005425935974, 'й': 0.004449267498643516,
               'ц': 0.010363537710255019, 'щ': 0.003581117742810635, 'ш': 0.005425935973955507,
               'ы': 0.0066196418882257186, 'ф': 0.006348345089527943, 'ю': 0.002984264785675529,
               'х': 0.005154639175257732, 'ъ': 0.0005968529571351058, 'э': 0.002278893109061313}


ROW_LENGTHS = [4, 5, 6, 7, 6, 5, 4]

CENTER_INDICES = [1.5, 2, 2.5, 3, 2.5, 2, 1.5]

class Game:
    def __init__(self, creator_id: str, radius: int = 7):
        self.players: List[Player] = []
        self.current_player_index = 0
        self.letters = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЧЦШЩЪЫЬЭЮЯ"
        # self.radius = self.prepare_radius(radius)
        self.radius = self.prepare_radius(7)
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
                    letter = random.choice(self.letters)
                    weight = random.randint(1, 5)
                    # new_row.append({"letter": f"{row[k]} {k}", "weight": weight, "clicks": 0})
                    new_row.append({"letter": "", "weight": weight, "clicks": 0})
                else:
                    new_row.append(None)

            grid.append(new_row)

        logger.info(f"Generated grid, cell [{center}][{center}]: {grid[center][center]}")

        # Шаг 3: Заполнение сетки
        def get_neighbors(row: int, col: int) -> List[Tuple[int, int]]:
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1)] if row % 2 == 0 else [(-1, 0), (1, 0),
                                                                                                     (0, -1), (0, 1),
                                                                                                     (-1, 1), (1, 1)]
            neighbors = []
            for dr, dc in directions:
                r, c = row + dr, col + dc
                if 0 <= r < 7 and 0 <= c < self.radius and grid[r][c] is not None:
                    neighbors.append((r, c))
            return neighbors

        # Заполнить центр
        grid[3][3]["letter"] = random.choices(list(letter_prob.keys()), weights=list(letter_prob.values()), k=1)[0]
        logger.info(f"Central cell [3][3]: {grid[3][3]['letter']}")

        # Заполнить остальные ячейки
        for i in range(7):
            offset = int(3.5 - CENTER_INDICES[i])
            for j in range(offset, offset + ROW_LENGTHS[i]):
                if grid[i][j]["letter"]:
                    continue
                neighbors = get_neighbors(i, j)
                neighbor_letters = [grid[r][c]["letter"] for r, c in neighbors if grid[r][c]["letter"]]
                if neighbor_letters:
                    candidates = []
                    weights = []
                    for letter in self.letters:
                        score = 0
                        for n_letter in neighbor_letters:
                            bigram1 = n_letter + letter
                            bigram2 = letter + n_letter
                            score += bigram_prob.get(bigram1, 0) + bigram_prob.get(bigram2, 0)
                        candidates.append(letter)
                        weights.append(score + letter_prob.get(letter, 0.001))
                    if sum(weights) == 0:
                        weights = [letter_prob.get(l, 0.001) for l in candidates]
                    grid[i][j]["letter"] = random.choices(candidates, weights=weights, k=1)[0]
                else:
                    grid[i][j]["letter"] = \
                    random.choices(list(letter_prob.keys()), weights=list(letter_prob.values()), k=1)[0]
                logger.info(f"Cell [{i}][{j}]: {grid[i][j]['letter']}, neighbors: {neighbor_letters}")

        # Шаг 4: Проверка количества слов
        def find_words(row: int, col: int, path: List[List[int]], word: str, used_cells: Set[Tuple[int, int]],
                       found_words: Set[str]):
            if word in DICTIONARY and word not in found_words:
                found_words.add(word)
            if len(word) >= 8:
                return
            next_cells = get_neighbors(row, col) + [(row, col)]  # Разрешить повторение
            for r, c in next_cells:
                if (r, c) in used_cells:
                    continue
                new_path = path + [[r, c]]
                new_word = word + grid[r][c]["letter"]
                new_used = used_cells | {(r, c)}
                find_words(r, c, new_path, new_word, new_used, found_words)

        found_words = set()
        for i in range(7):
            for j in range(self.radius):
                if grid[i][j] is not None:
                    find_words(i, j, [[i, j]], grid[i][j]["letter"], {(i, j)}, found_words)
        logger.info(f"Found words: {found_words}")

        # Шаг 5: Оптимизация
        if len(found_words) < 10:
            logger.info("Optimizing grid: too few words")
            for i in range(7):
                for j in range(self.radius):
                    if grid[i][j] is None:
                        continue
                    neighbors = get_neighbors(i, j)
                    neighbor_letters = [grid[r][c]["letter"] for r, c in neighbors if grid[r][c]["letter"]]
                    candidates = []
                    weights = []
                    for letter in self.letters:
                        score = 0
                        for n_letter in neighbor_letters:
                            bigram1 = n_letter + letter
                            bigram2 = letter + n_letter
                            score += bigram_prob.get(bigram1, 0) + bigram_prob.get(bigram2, 0)
                        candidates.append(letter)
                        weights.append(score + letter_prob.get(letter, 0.001))
                    if sum(weights) > 0:
                        grid[i][j]["letter"] = random.choices(candidates, weights=weights, k=1)[0]
                        logger.info(f"Optimized cell [{i}][{j}]: {grid[i][j]['letter']}")

        logger.info(f"Final grid generated, total words: {len(found_words)}")

        return grid

    def add_player(self, player_id: str, name: str, websocket: Union[WebSocket, None]):

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
        # global USED_WORDS

        word = word.upper()

        current_player = self.players[self.current_player_index]
        if current_player.id != player_id:
            logger.warning(f"Invalid word submission: player_id={player_id} is not current player={current_player.id}")
            return {"valid": False, "reason": "Ход противника", "word": word}

        if not self.is_valid_path(path):
            current_player.lives -= 1
            logger.info(f"Invalid path for word: {word}, player_id={player_id}, lives={current_player.lives}")
            return {"valid": False, "reason": "Invalid path", "word": word}

        # Проверяем существует ли слово
        is_exist = word_checker.check_word(word).is_exist

        if word is is_exist:
            current_player.lives -= 1
            logger.info(f"Word not in dictionary: {word}, player_id={player_id}, lives={current_player.lives}")
            return {"valid": False, "reason": "Такое слово не найдено", "word": word}

        if word in USED_WORDS:
            current_player.lives -= 1
            logger.info(f"Word already used: {word}, player_id={player_id}, lives={current_player.lives}")
            return {"valid": False, "reason": "Слово уже было найдено", "word": word}

        score = sum(self.grid[r][c]["weight"] for r, c in path)
        current_player.score += score
        current_player.words.append(word)
        USED_WORDS.add(word)

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
