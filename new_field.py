import random
from typing import List, Dict, Set, Tuple
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Словарь и алфавит
DICTIONARY = {"кот", "дом", "сад", "лес", "мир", "книга", "стол", "окно"}  # Расширьте словарь
LETTERS = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
ROW_LENGTHS = [4, 5, 6, 7, 6, 5, 4]
MAX_COLS = 7
CENTER_INDICES = [1.5, 2, 2.5, 3, 2.5, 2, 1.5]

def generate_grid() -> List[List[Dict]]:
    """
    Генерирует гексагональное поле с буквами, максимизируя количество возможных слов.
    """
    # Шаг 1: Частотный анализ
    letter_freq = {}
    bigram_freq = {}
    for word in DICTIONARY:
        for letter in word:
            letter_freq[letter] = letter_freq.get(letter, 0) + 1
        for i in range(len(word) - 1):
            bigram = word[i:i+2]
            bigram_freq[bigram] = bigram_freq.get(bigram, 0) + 1
    total_letters = sum(letter_freq.values()) or 1
    letter_prob = {k: v / total_letters for k, v in letter_freq.items()}
    total_bigrams = sum(bigram_freq.values()) or 1
    bigram_prob = {k: v / total_bigrams for k, v in bigram_freq.items()}
    logger.info(f"Letter probabilities: {letter_prob}")
    logger.info(f"Bigram probabilities: {bigram_freq}")

    # Шаг 2: Создание пустой сетки
    grid = [[None] * MAX_COLS for _ in range(7)]
    for i, num_cells in enumerate(ROW_LENGTHS):
        offset = int(3.5 - CENTER_INDICES[i])
        for j in range(offset, offset + num_cells):
            grid[i][j] = {"letter": "", "weight": random.randint(1, 5), "clicks": 0}

    # Шаг 3: Заполнение сетки
    def get_neighbors(row: int, col: int) -> List[Tuple[int, int]]:
        directions = [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (1,-1)] if row % 2 == 0 else [(-1,0), (1,0), (0,-1), (0,1), (-1,1), (1,1)]
        neighbors = []
        for dr, dc in directions:
            r, c = row + dr, col + dc
            if 0 <= r < 7 and 0 <= c < MAX_COLS and grid[r][c] is not None:
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
                for letter in LETTERS:
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
                grid[i][j]["letter"] = random.choices(list(letter_prob.keys()), weights=list(letter_prob.values()), k=1)[0]
            logger.info(f"Cell [{i}][{j}]: {grid[i][j]['letter']}, neighbors: {neighbor_letters}")

    # Шаг 4: Проверка количества слов
    def find_words(row: int, col: int, path: List[List[int]], word: str, used_cells: Set[Tuple[int, int]], found_words: Set[str]):
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
        for j in range(MAX_COLS):
            if grid[i][j] is not None:
                find_words(i, j, [[i, j]], grid[i][j]["letter"], {(i, j)}, found_words)
    logger.info(f"Found words: {found_words}")

    # Шаг 5: Оптимизация
    if len(found_words) < 10:
        logger.info("Optimizing grid: too few words")
        for i in range(7):
            for j in range(MAX_COLS):
                if grid[i][j] is None:
                    continue
                neighbors = get_neighbors(i, j)
                neighbor_letters = [grid[r][c]["letter"] for r, c in neighbors if grid[r][c]["letter"]]
                candidates = []
                weights = []
                for letter in LETTERS:
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