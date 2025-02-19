import os
import re
import math
import sys
import random

# Параметры отображения: размеры блока клетки
CELL_WIDTH = 10    # ширина блока в символах
CELL_HEIGHT = 5    # высота блока: 3 строки для арта, 1 пустая, 1 строка для статов

# Исходное ASCII‑поле с пронумерованными разрешёнными клетками (например, @1, @2, @3, @4, …)
FIELD = r"""
..........................................################..........................................
..................................########........#.......########..................................
..............................####................#...............####..............................
..........................####....................#...................####..........................
.......................###........................#.......................###.......................
....................##....#.......................#......................#....##....................
..................#........#......................#.....................#........#..................
................#...........#.....................#....................#...........#................
..............#..............#...........@1.......#........@2.........#..............#..............
............##................#................#######...............#................##............
...........#...................##....##########...#...#########.....#...................#...........
..........#.....................##.##.............#............##..#.....................#..........
........#.......................###...............#...............##.......................#........
.......#......................#....#..............#..............#...#......................#.......
......###...................#.......#.............#............##......#...................###......
.....#....##........@3....#..........#............#...........##.........#.....@4.......##....#.....
....#.........##........#.............#...........#..........##............#.........##........#....
....#............##....#...............#..........#.........##..............#.....##...........#....
...#................###.................#......@6.#....@7..#.................###................#...
..#..................#.##................#......####......#................##.#..................#..
..#.................#.....+#......@5......###..........###......@8......##.....#.................#..
.-.................#..........##........##................##.........##.........#.................#.
.#.................#.............##....#....................#.....#.............#.................#.
.#................#.................##........................##.................#................#.
..................#.................##........................##.................#.................#
#........@9.......#.......@A........#..........................#.........@B......#........@C.......#
#................#.................##...........................#.................#................#
####################################...............@0...........####################################
#................#.................#............................#.................#................#
#.................#.................#..........................#.................#.................#
-.................#.................#..........................#.................#.................#
.#................#.................##........................##.................#................#.
.#.................#..............#...##....................##...##.............#.................#.
.#.................#......@E..##........#..................#........##....@J....#.................#.
..#.................#......##.............##............##..............#......#.................#..
..#..................#..##...............#.....######.....#................##.#..................#..
...#.......@D........##.................#.........#........#.................###.........@K.....#...
....#............##+...#...............#..........#.........#...............#....##.................
....#.........##........#.............#...........#..........#.............#........##.........#....
.....#.....##............-#.....@F...#............#...........#......@I..##............##.....#.....
......#.##.................##.......#.............#............#.......##..................###......
.......#.....................##....#..............#.............##...##.....................#.......
........#.......................###.........@G....#.......@H.....###.......................#........
.........##......................#.##.............#............+#..#.....................##.........
...........#.........@L.........#......########...#..########.......#..........@O.......#...........
............#+................##...............######................#................-#............
..............#..............##...................#...................#..............#..............
................#...........#-....................#....................#...........#................
..................#........#......................#.....................#........#..................
....................##....#.......................#......................#....##....................
.......................#.#........................#.......................#-#.......................
.........................-##.............@M.......#..........@N.........###.........................
.............................##...................#..................##.............................
.................................#######..........#.........#######.................................
........................................####################........................................
"""

# Разбиваем поле на строки и выравниваем их по ширине
FIELD_LINES = [line for line in FIELD.splitlines() if line.strip() != ""]
max_width = max(len(line) for line in FIELD_LINES)
canvas_original = [list(line.ljust(max_width)) for line in FIELD_LINES]
CANVAS_HEIGHT = len(canvas_original)
CANVAS_WIDTH = len(canvas_original[0]) if canvas_original else 0

# Парсим разрешённые клетки: ищем вхождения вида "@<символ>"
allowed_cells = {}  # ключ: метка (строка), значение: (row, col)
for r, line in enumerate(FIELD_LINES):
    for m in re.finditer(r'@([0-9A-Z])', line):
        label = m.group(1)
        c = m.start()
        allowed_cells[label] = (r, c)

# Игровой стол: ключ – метка клетки, значение – токен или None
board = {label: None for label in allowed_cells}

# Жёстко заданный словарь соседей (куда можно переместиться/атаковать)
neighbors_map = {
    '0': ['A', 'B', 'F', 'G', 'H', '5', '6', '7', '8', 'J', 'I', 'E'],
    '1': ['2', '5', '6', '3', '7'],
    '2': ['1', '6', '7', '8', '4'],
    '3': ['9', 'A', '5', '6', '1'],
    '4': ['2', '7', '8', 'B', 'C'],
    '5': ['1', '6', 'A', '3', '9', '0'],
    '6': ['1', '2', '5', '3', '7', '0'],
    '7': ['2', '1', '6', '8', '4', '0'],
    '8': ['7', '2', '4', 'C', 'B', '0'],
    '9': ['D', 'E', 'A', '5', '3'],
    'A': ['3', '9', 'D', 'E', '5', '0'],
    'B': ['8', '4', 'C', 'K', 'J', '0'],
    'C': ['4', '8', 'B', 'K', 'J'],
    'D': ['9', 'A', 'E', 'F', 'L'],
    'E': ['A', '9', 'D', 'L', 'F', '0'],
    'F': ['E', 'D', 'L', 'M', 'G', '0'],
    'G': ['F', 'L', 'M', 'N', 'H', '0'],
    'H': ['G', 'M', 'N', 'O', 'I', '0'],
    'I': ['H', 'N', 'O', 'K', 'J', '0'],
    'J': ['I', 'O', '0', 'K', 'C', 'B'],
    'K': ['O', 'I', 'J', 'B', 'C'],
    'L': ['D', 'E', 'F', 'G', 'M'],
    'M': ['L', 'F', 'G', 'H', 'N'],
    'N': ['M', 'G', 'H', 'I', 'O'],
    'O': ['N', 'H', 'I', 'J', 'K']
}

# ASCII‑арт токенов (улучшенные рисунки)
def get_soldier_art():
    return [
        "..//\\.╋.",
        ".//==╘║.",
        "..\\//.║."
    ]
def get_archer_art():
    return [
        "...O..⎫",
        "..╘┼╘─┆→",
        "../.\\.⎭"
    ]
def get_knight_art():
    return [
        "...O...",
        "../|╘─┄┄",
        "../.\\..."
    ]
def get_mage_art():
    return [
        "...O ◆..",
        "../|╘┃..",
        "..⎧║⎫┃.."
    ]
token_arts = {
    "Soldier": get_soldier_art(),
    "Archer": get_archer_art(),
    "Knight": get_knight_art(),
    "Mage": get_mage_art()
}

# Функция для проверки, сможет ли attacker убить defender (без контратак)
def can_kill(attacker, defender):
    if attacker.attack > defender.defense:
        potential = attacker.attack - defender.defense
    else:
        potential = attacker.attack // 2
    return potential >= defender.hp

# Класс токена с добавлением max_hp, cooldown, frozen, knockback_cooldown и shield_repair_cooldown для солдата,
# а также специального флага для рыцаря (special_used)
class Token:
    def __init__(self, side, tclass, hp, attack, defense):
        self.side = side
        self.tclass = tclass
        self.hp = hp
        self.max_hp = hp
        self.attack = attack
        self.defense = defense
        self.frozen = 0
        if tclass in ["Mage", "Archer"]:
            self.cooldown = 0
        else:
            self.cooldown = None
        if tclass == "Knight":
            self.special_used = False
        else:
            self.special_used = None
        if tclass == "Soldier":
            self.knockback_cooldown = 0  # Способность отбрасывания доступна, если 0
            self.shield_repair_cooldown = 0  # Способность ремонта щита доступна, если 0
            self.max_defense = defense  # Максимальный щит (не может быть восстановлен выше него)
        else:
            self.knockback_cooldown = None
            self.shield_repair_cooldown = None
            self.max_defense = None
    def __str__(self):
        return f"{self.tclass} (H:{self.hp} A:{self.attack} D:{self.defense})"

# Формирование блока для токена (ASCII‑арт + статы)
def token_block(token, spaced=True):
    block = []
    art = token_arts[token.tclass]
    art_lines = art + [""] * (3 - len(art))
    for line in art_lines[:3]:
        if spaced:
            block.append(line.center(CELL_WIDTH))
        else:
            block.append(line)
    if spaced:
        block.append(" " * CELL_WIDTH)
    else:
        block.append("")
    stats = f"H:{token.hp} A:{token.attack} D:{token.defense}"
    if token.frozen > 0:
        stats += " [F]"
    if spaced:
        block.append(stats.center(CELL_WIDTH))
    else:
        block.append(stats)
    return block

# Наложение блока токена на canvas: нижняя центральная точка блока совпадает с координатой клетки
def overlay_token(canvas, cell_label, block):
    r_anchor, c_anchor = allowed_cells[cell_label]
    top = r_anchor - (CELL_HEIGHT - 1)
    left = c_anchor - (CELL_WIDTH // 2)
    for i, line in enumerate(block):
        for j, ch in enumerate(line):
            y = top + i
            x = left + j
            if 0 <= y < CANVAS_HEIGHT and 0 <= x < CANVAS_WIDTH:
                canvas[y][x] = ch

# Отрисовка поля: если клетка пуста, выводим её метку (отцентрированную в блоке)
def print_board():
    canvas = [row[:] for row in canvas_original]
    LABEL_WIDTH = 5  # отступы по 2 символа с каждой стороны для меток клеток
    for cell_label, coord in allowed_cells.items():
        if board.get(cell_label) is None:
            r_anchor, c_anchor = coord
            top = r_anchor - (CELL_HEIGHT - 1)
            left = c_anchor - (CELL_WIDTH // 2)
            label = cell_label.center(LABEL_WIDTH)
            label_left = left + (CELL_WIDTH - LABEL_WIDTH) // 2
            for i, ch in enumerate(label):
                y = top + CELL_HEIGHT - 1
                x = label_left + i
                if 0 <= y < CANVAS_HEIGHT and 0 <= x < CANVAS_WIDTH:
                    canvas[y][x] = ch
    # Наложение персонажей без пробелов
    for cell_label, token in board.items():
        if token is not None:
            block = token_block(token, spaced=False)
            overlay_token(canvas, cell_label, block)
    os.system("cls")
    for line in canvas:
        print("".join(line))

# Функция выбора варианта из списка с возможностью завершить игру
def choose_option(prompt, options):
    if not options:
        return None
    for i, option in enumerate(options, start=1):
        print(f"{i}: {option}")
    print("0: Завершить игру")
    while True:
        inp = input(prompt)
        if inp.strip().lower() in ['0', 'q', 'quit']:
            print("Завершение игры.")
            sys.exit(0)
        try:
            choice = int(inp)
            if 1 <= choice <= len(options):
                return options[choice - 1]
            else:
                print("Неверный номер, попробуйте снова.")
        except ValueError:
            print("Введите число, соответствующее номеру.")

# Функция вычисления расширённых целей атаки:
def extended_targets(source_label):
    ext = set(neighbors_map.get(source_label, []))
    for nbr in neighbors_map.get(source_label, []):
        ext.update(neighbors_map.get(nbr, []))
    ext.add(source_label)
    return list(ext)

# Функция для расширённой атаки мага (для Archer аналогична)
def extended_attack(attacker, source_label, current_turn):
    targets = extended_targets(source_label)
    enemy_targets = [t for t in targets if board.get(t) is not None and board[t].side != current_turn]
    if not enemy_targets:
        print("Нет доступных расширённых целей для атаки.")
        return
    print("\nДоступные расширённые цели для атаки:")
    enemy_options = [f"{board[t].tclass} на клетке {t} (H:{board[t].hp} A:{board[t].attack} D:{board[t].defense})" for t in enemy_targets]
    target1 = choose_option("Выберите клетку для первой атаки: ", enemy_options)
    target_label1 = None
    for t, opt in zip(enemy_targets, enemy_options):
        if opt == target1:
            target_label1 = t
            break
    result = combat(attacker, board[target_label1], allow_counterattack=False)
    if result == "defender_dead":
        board[target_label1] = None
    elif result == "attacker_dead":
        board[source_label] = None
        return
    remaining = [t for t in enemy_targets if t != target_label1 and board.get(t) is not None and board[t].side != current_turn]
    if remaining:
        if input("Желаете атаковать вторую цель? (y/n): ").strip().lower() == 'y':
            enemy_options2 = [f"{board[t].tclass} на клетке {t} (H:{board[t].hp} A:{board[t].attack} D:{board[t].defense})" for t in remaining]
            target2 = choose_option("Выберите клетку для второй атаки: ", enemy_options2)
            target_label2 = None
            for t, opt in zip(remaining, enemy_options2):
                if opt == target2:
                    target_label2 = t
                    break
            result = combat(attacker, board[target_label2], allow_counterattack=False)
            if result == "defender_dead":
                board[target_label2] = None
            elif result == "attacker_dead":
                board[source_label] = None

# Функция специального удара для рыцаря (2x damage), используется один раз за игру
def knight_special_attack(attacker, defender, allow_counterattack=True):
    special_attack_value = 2 * attacker.attack
    raw_dmg = special_attack_value - defender.defense
    if raw_dmg > 0:
        dmg = raw_dmg
        print(f"{attacker.tclass} (спец. удар) наносит {dmg} урона {defender.tclass} (щит пробит).")
        defender.hp -= dmg
        if defender.hp <= 0:
            print(f"{defender.tclass} побеждён!")
            return "defender_dead"
        if allow_counterattack:
            counter = max(defender.attack - attacker.defense, 0)
            print(f"{defender.tclass} контратакует и пытается нанести {counter} урона {attacker.tclass}.")
            apply_damage(attacker, counter)
            if attacker.hp <= 0:
                print(f"{attacker.tclass} побеждён в контратаке!")
                return "attacker_dead"
        return "both_alive"
    else:
        special_dmg = special_attack_value // 2
        print(f"{attacker.tclass} (спец. удар) пробивает щит {defender.tclass} и наносит {special_dmg} повреждений щиту.")
        defender.defense -= special_dmg
        if defender.defense < 0:
            defender.defense = 0
        if allow_counterattack:
            counter = defender.attack // 2
            print(f"{defender.tclass} контратакует и пытается нанести {counter} урона {attacker.tclass}.")
            apply_damage(attacker, counter)
            if attacker.hp <= 0:
                print(f"{attacker.tclass} побеждён в контратаке!")
                return "attacker_dead"
        return "both_alive"

# Функция специального отбрасывающего удара для солдата (2x damage и отбрасывание в соседнюю пустую клетку)
def soldier_knockback_attack(attacker, defender, defender_cell):
    print(f"{attacker.tclass} использует отбрасывающую атаку!")
    result = knight_special_attack(attacker, defender, allow_counterattack=False)
    if result == "defender_dead":
        # Попытаемся отбросить врага: ищем пустую соседнюю клетку для врага
        enemy_cell = None
        for nbr in neighbors_map.get(defender_cell, []):  # defender_cell – клетка, где стоял враг
            if board.get(nbr) is None:
                enemy_cell = nbr
                break
        if enemy_cell:
            print(f"Враг отбит на клетку {enemy_cell}.")
            board[enemy_cell] = defender
            board[defender_cell] = None
        return result
    # Независимо от результата, устанавливаем cooldown
    attacker.knockback_cooldown = 7
    return result
    # Устанавливаем cooldown
    attacker.knockback_cooldown = 7
    return result

    # Независимо от результата, устанавливаем cooldown
    attacker.knockback_cooldown = 7
    return result

# Функция применения урона с учётом разрушаемого щита
def apply_damage(target, damage):
    if damage <= target.defense:
        reduction = damage // 2
        target.defense -= reduction
        if target.defense < 0:
            target.defense = 0
        print(f"Щит {target.tclass} уменьшен на {reduction} (новый щит: {target.defense}).")
    else:
        remainder = damage - target.defense
        print(f"Щит {target.tclass} пробит (щит: {target.defense}), остаток урона: {remainder}.")
        target.defense = 0
        target.hp -= remainder

# Функция стандартного combat с разрушаемым щитом
def combat(attacker, defender, allow_counterattack=True):
    raw_dmg = attacker.attack - defender.defense
    if raw_dmg > 0:
        dmg = raw_dmg
        print(f"{attacker.tclass} наносит {dmg} урона {defender.tclass} (щит пробит).")
        defender.hp -= dmg
        if defender.hp <= 0:
            print(f"{defender.tclass} побеждён!")
            return "defender_dead"
        if allow_counterattack:
            counter = max(defender.attack - attacker.defense, 0)
            print(f"{defender.tclass} контратакует и пытается нанести {counter} урона {attacker.tclass}.")
            apply_damage(attacker, counter)
            if attacker.hp <= 0:
                print(f"{attacker.tclass} побеждён в контратаке!")
                return "attacker_dead"
        return "both_alive"
    special_dmg = attacker.attack // 2
    print(f"{attacker.tclass} пробивает щит {defender.tclass} и наносит {special_dmg} повреждений щиту.")
    defender.defense -= special_dmg
    if defender.defense < 0:
        defender.defense = 0
    if allow_counterattack:
        counter = defender.attack // 2
        print(f"{defender.tclass} контратакует и пытается нанести {counter} урона {attacker.tclass}.")
        apply_damage(attacker, counter)
        if attacker.hp <= 0:
            print(f"{attacker.tclass} побеждён в контратаке!")
            return "attacker_dead"
    return "both_alive"

# Инициализация токенов
# Для команды Blue:
#   Soldier на "3": HP=10, ATK=5, DEF=4 (увеличим DEF для демонстрации ремонта)
#   Mage на "4": HP=6, ATK=6, DEF=2
#   Knight на "C": HP=5, ATK=4, DEF=8
#   Archer на "2": HP=4, ATK=7, DEF=1
board["3"] = Token('B', "Soldier", 10, 5, 4)
board["4"] = Token('B', "Mage", 6, 6, 2)
board["C"] = Token('B', "Knight", 5, 4, 8)
board["2"] = Token('B', "Archer", 4, 7, 1)

# Для команды Red:
#   Soldier на "L": HP=10, ATK=5, DEF=4
#   Mage на "O": HP=6, ATK=6, DEF=2
#   Knight на "K": HP=5, ATK=4, DEF=8
#   Archer на "N": HP=4, ATK=7, DEF=1
board["L"] = Token('R', "Soldier", 10, 5, 4)
board["O"] = Token('R', "Mage", 6, 6, 2)
board["K"] = Token('R', "Knight", 5, 4, 8)
board["N"] = Token('R', "Archer", 4, 7, 1)

# Функция получения доступных клеток для перемещения для токена,
# с учётом возможности пойти на клетку с врагом, если можно его убить
# Функция получения доступных клеток для перемещения для токена,
# с учётом возможности пойти на клетку с врагом, если можно его убить
# Для солдата с готовой способностью knockback (knockback_cooldown == 0) добавляем вражеские клетки независимо от can_kill.
def get_available_moves(cell_label, token):
    empty_moves = [nbr for nbr in neighbors_map.get(cell_label, []) if board.get(nbr) is None]
    enemy_moves = []
    for nbr in neighbors_map.get(cell_label, []):
        if board.get(nbr) is not None and board[nbr].side != token.side:
            if token.tclass == "Soldier" and token.knockback_cooldown == 0:
                enemy_moves.append(nbr)
            else:
                if can_kill(token, board[nbr]):
                    enemy_moves.append(nbr)
    return empty_moves + enemy_moves

# Обновление заморозки и cooldown'ов для солдат
def update_cooldowns():
    for token in board.values():
        if token is not None:
            if token.frozen > 0:
                token.frozen -= 1
            if token.tclass == "Soldier":
                if token.knockback_cooldown > 0:
                    token.knockback_cooldown -= 1
                if token.shield_repair_cooldown > 0:
                    token.shield_repair_cooldown -= 1

# Функция для специального отбрасывающего удара солдата
def soldier_knockback_attack(attacker, defender, attacker_cell, defender_cell):
    print(f"{attacker.tclass} использует отбрасывающую атаку!")
    # Удаляем атакующего солдата с его исходной клетки, чтобы избежать клонирования
    board[attacker_cell] = None
    # Солдат наносит ровно 2 единицы урона
    damage = 2
    defender.hp -= damage
    print(f"{attacker.tclass} наносит 2 урона {defender.tclass}.")
    if defender.hp <= 0:
        print(f"{defender.tclass} побеждён!")
        # Перемещаем солдата на клетку противника
        board[defender_cell] = attacker
        attacker.knockback_cooldown = 7
        return "defender_dead"
    # Если враг жив, пытаемся отбросить его: ищем пустую соседнюю клетку для врага
    empty_neighbors = [nbr for nbr in neighbors_map.get(defender_cell, []) if board.get(nbr) is None]
    if empty_neighbors:
        new_cell = random.choice(empty_neighbors)
        print(f"Враг отбит на клетку {new_cell}.")
        board[new_cell] = defender
        board[defender_cell] = None
    else:
        print("Нет свободной клетки для отбрасывания врага, враг остается на месте.")
    # Затем солдат занимает клетку, где стоял враг
    board[defender_cell] = attacker
    attacker.knockback_cooldown = 7
    return "both_alive"

# Функция ремонта щита для солдата (25% от max_defense, но не выше max_defense)
def repair_shield(token):
    repair_amount = max(1, int(0.25 * token.max_defense))
    new_def = min(token.defense + repair_amount, token.max_defense)
    print(f"{token.tclass} ремонтирует щит: {token.defense} -> {new_def}.")
    token.defense = new_def
    token.shield_repair_cooldown = 6

# Функция для расширённой атаки мага (для Archer аналогична)
def extended_attack(attacker, source_label, current_turn):
    targets = extended_targets(source_label)
    enemy_targets = [t for t in targets if board.get(t) is not None and board[t].side != current_turn]
    if not enemy_targets:
        print("Нет доступных расширённых целей для атаки.")
        return
    print("\nДоступные расширённые цели для атаки:")
    enemy_options = [f"{board[t].tclass} на клетке {t} (H:{board[t].hp} A:{board[t].attack} D:{board[t].defense})" for t in enemy_targets]
    target1 = choose_option("Выберите клетку для первой атаки: ", enemy_options)
    target_label1 = None
    for t, opt in zip(enemy_targets, enemy_options):
        if opt == target1:
            target_label1 = t
            break
    result = combat(attacker, board[target_label1], allow_counterattack=False)
    if result == "defender_dead":
        board[target_label1] = None
    elif result == "attacker_dead":
        board[source_label] = None
        return
    remaining = [t for t in enemy_targets if t != target_label1 and board.get(t) is not None and board[t].side != current_turn]
    if remaining:
        if input("Желаете атаковать вторую цель? (y/n): ").strip().lower() == 'y':
            enemy_options2 = [f"{board[t].tclass} на клетке {t} (H:{board[t].hp} A:{board[t].attack} D:{board[t].defense})" for t in remaining]
            target2 = choose_option("Выберите клетку для второй атаки: ", enemy_options2)
            target_label2 = None
            for t, opt in zip(remaining, enemy_options2):
                if opt == target2:
                    target_label2 = t
                    break
            result = combat(attacker, board[target_label2], allow_counterattack=False)
            if result == "defender_dead":
                board[target_label2] = None
            elif result == "attacker_dead":
                board[source_label] = None

# Функция вычисления расширённых целей атаки
def extended_targets(source_label):
    ext = set(neighbors_map.get(source_label, []))
    for nbr in neighbors_map.get(source_label, []):
        ext.update(neighbors_map.get(nbr, []))
    ext.add(source_label)
    return list(ext)

# Функция выбора действия для мага
def mage_attack_menu(attacker, source_label, current_turn):
    print("\nВарианты атаки мага:")
    options = ["Огненный шар", "Заморозка"]
    if attacker.cooldown == 0:
        options.append("Хилл")
    else:
        options.append(f"Хилл (не доступен, {attacker.cooldown} ход(ов) до восстановления)")
    mage_choice = choose_option("Выберите действие мага: ", options)
    if "Огненный шар" in mage_choice:
        print("Вы выбрали Огненный шар.")
        extended_attack(attacker, source_label, current_turn)
    elif "Заморозка" in mage_choice:
        print("Вы выбрали Заморозку.")
        targets = extended_targets(source_label)
        enemy_targets = [t for t in targets if board.get(t) is not None and board[t].side != current_turn]
        if enemy_targets:
            print("\nДоступные цели для заморозки:")
            enemy_options = [f"{board[t].tclass} на клетке {t} (H:{board[t].hp})" for t in enemy_targets]
            target = choose_option("Выберите клетку для заморозки: ", enemy_options)
            target_label = None
            for t, opt in zip(enemy_targets, enemy_options):
                if opt == target:
                    target_label = t
                    break
            print(f"{board[target_label].tclass} на клетке {target_label} заморожен на 1 ход!")
            board[target_label].frozen = 1
        else:
            print("Нет доступных целей для заморозки.")
    elif "Хилл" in mage_choice:
        if attacker.cooldown == 0:
            allies = [(cell, token) for cell, token in board.items() 
                      if token is not None and token.side == current_turn and token.hp < token.max_hp]
            if allies:
                print("Доступные союзники для лечения (если не выбрать, лечится маг):")
                ally_options = [f"{token.tclass} на клетке {cell} (H:{token.hp}/{token.max_hp})" for cell, token in allies]
                ally_choice = choose_option("Выберите союзника для лечения: ", ally_options)
                target_cell = None
                for cell, token in allies:
                    option_str = f"{token.tclass} на клетке {cell} (H:{token.hp}/{token.max_hp})"
                    if option_str == ally_choice:
                        target_cell = cell
                        break
                if target_cell:
                    print(f"{attacker.tclass} лечит союзника на клетке {target_cell} на 2 HP.")
                    board[target_cell].hp = min(board[target_cell].hp + 2, board[target_cell].max_hp)
                else:
                    print("Союзник не выбран. Лечится маг.")
                    attacker.hp = min(attacker.hp + 2, attacker.max_hp)
            else:
                print("Нет союзников, нуждающихся в лечении. Лечится маг.")
                attacker.hp = min(attacker.hp + 2, attacker.max_hp)
            attacker.cooldown = 5
        else:
            print("Хилл недоступен.")
    if attacker.cooldown is not None and attacker.cooldown > 0:
        attacker.cooldown -= 1

# Основной игровой цикл
def main():
    current_turn = 'B'  # Blue начинают
    while True:
        update_freeze()
        print_board()
        # Обновляем cooldown для солдат
        update_cooldowns()
        blue_exists = any(token is not None and token.side == 'B' for token in board.values())
        red_exists = any(token is not None and token.side == 'R' for token in board.values())
        if not blue_exists or not red_exists:
            winner = 'B' if blue_exists else 'R'
            print(f"\nПобедили {'Синие' if winner=='B' else 'Красные'}!")
            break

        side_name = "Синие" if current_turn == 'B' else "Красные"
        print(f"\nХод {side_name}.")

        # Выбор токена текущего игрока (все, отмечая замороженные)
        available_tokens = [(cell, token) for cell, token in board.items() if token is not None and token.side == current_turn]
        if not available_tokens:
            print("Нет токенов для перемещения.")
            break
        print("\nВаши токены:")
        token_options = []
        for cell, token in available_tokens:
            option_str = f"{token.tclass} на клетке {cell} (H:{token.hp} A:{token.attack} D:{token.defense})"
            if token.frozen > 0:
                option_str += " (Заморожена)"
            token_options.append(option_str)
        # Запрашиваем выбор, если выбран замороженный – просим выбрать другого
        while True:
            chosen = choose_option("Выберите номер токена для перемещения: ", token_options)
            chosen_index = token_options.index(chosen)
            chosen_cell, moving_token = available_tokens[chosen_index]
            if moving_token.frozen > 0:
                print("Эта фишка заморожена и не может ходить. Выберите другую.")
                input("Нажмите Enter для продолжения...")
            else:
                break

        # Получаем доступные варианты перемещения
        moves = get_available_moves(chosen_cell, moving_token)
        # Если солдат и его способность ремонта щита готова, добавляем вариант ремонта
        if moving_token.tclass == "Soldier" and moving_token.shield_repair_cooldown == 0:
            moves.append("repair")
        moves.append("skip")
        print("\nДоступные варианты перемещения:")
        move_options = []
        for move in moves:
            if move == "skip":
                move_options.append("Пропустить движение")
            elif move == "repair":
                move_options.append("Ремонт щита")
            else:
                move_options.append(f"Клетка {move}")
        dest_choice = choose_option("Выберите вариант перемещения: ", move_options)
        if dest_choice == "Пропустить движение":
            destination = chosen_cell
            print(f"\nДвижение пропущено. Токен остаётся на клетке {chosen_cell}.")
        elif dest_choice == "Ремонт щита":
            destination = chosen_cell
            repair_shield(moving_token)
        else:
            destination = dest_choice.split()[-1]
            # Если на выбранной клетке стоит враг
            if board.get(destination) is not None:
                if moving_token.tclass == "Soldier" and moving_token.knockback_cooldown == 0:
                    print(f"\nНа клетке {destination} стоит враг. Выберите тип боя:")
                    battle_options = ["Обычный бой", "Отбрасывающая атака"]
                    battle_choice = choose_option("Выберите тип атаки: ", battle_options)
                    if "Отбрасывающая" in battle_choice:
                        defender_cell = destination
                        result = soldier_knockback_attack(moving_token, board[destination], chosen_cell, destination)
                        if result == "defender_dead":
                            board[destination] = moving_token
                        elif result == "attacker_dead":
                            board[chosen_cell] = None
                            destination = None
                    else:
                        result = combat(moving_token, board[destination])
                        if result == "defender_dead":
                            board[destination] = moving_token
                        elif result == "attacker_dead":
                            board[chosen_cell] = None
                            destination = None

            else:
                board[chosen_cell] = None
                board[destination] = moving_token
                print(f"\n{moving_token.tclass} перемещён с клетки {chosen_cell} на клетку {destination}.")

        # Фаза атаки:
        if moving_token is not None and destination is not None:
            if moving_token.tclass == "Knight":
                attackable = [cell for cell in neighbors_map.get(destination, []) 
                              if board.get(cell) is not None and board[cell].side != current_turn]
                if attackable:
                    print("\nДоступные клетки для атаки:")
                    enemy_options = [f"{board[cell].tclass} на клетке {cell} (H:{board[cell].hp} A:{board[cell].attack} D:{board[cell].defense})" 
                                     for cell in attackable]
                    target = choose_option("Выберите клетку для атаки: ", enemy_options)
                    target_cell = None
                    for cell, opt in zip(attackable, enemy_options):
                        if opt == target:
                            target_cell = cell
                            break
                    knight_options = ["Обычный удар"]
                    if not moving_token.special_used:
                        knight_options.append("Специальный удар (2x damage)")
                    knight_choice = choose_option("Выберите тип удара: ", knight_options)
                    if "Обычный" in knight_choice:
                        result = combat(moving_token, board[target_cell])
                    else:
                        result = knight_special_attack(moving_token, board[target_cell])
                        moving_token.special_used = True
                    if result == "defender_dead":
                        board[target_cell] = None
                    elif result == "attacker_dead":
                        board[destination] = None
            elif moving_token.tclass != "Mage":
                attackable = [cell for cell in neighbors_map.get(destination, []) 
                              if board.get(cell) is not None and board[cell].side != current_turn]
                if attackable:
                    print("\nДоступные клетки для атаки:")
                    enemy_options = [f"{board[cell].tclass} на клетке {cell} (H:{board[cell].hp} A:{board[cell].attack} D:{board[cell].defense})" 
                                     for cell in attackable]
                    if input("Желаете атаковать? (y/n): ").strip().lower() == 'y':
                        target = choose_option("Выберите клетку для атаки: ", enemy_options)
                        target_cell = None
                        for cell, opt in zip(attackable, enemy_options):
                            if opt == target:
                                target_cell = cell
                                break
                        result = combat(moving_token, board[target_cell])
                        if result == "defender_dead":
                            board[target_cell] = None
                        elif result == "attacker_dead":
                            board[destination] = None
            else:
                mage_options = ["Огненный шар", "Заморозка"]
                if moving_token.cooldown == 0:
                    mage_options.append("Хилл")
                else:
                    mage_options.append(f"Хилл (не доступен, {moving_token.cooldown} ход(ов) до восстановления)")
                mage_choice = choose_option("Выберите действие мага: ", mage_options)
                if "Огненный шар" in mage_choice:
                    print("Вы выбрали Огненный шар.")
                    extended_attack(moving_token, destination, current_turn)
                elif "Заморозка" in mage_choice:
                    print("Вы выбрали Заморозку.")
                    targets = extended_targets(destination)
                    enemy_targets = [t for t in targets if board.get(t) is not None and board[t].side != current_turn]
                    if enemy_targets:
                        print("\nДоступные цели для заморозки:")
                        enemy_options = [f"{board[t].tclass} на клетке {t} (H:{board[t].hp})" for t in enemy_targets]
                        target = choose_option("Выберите клетку для заморозки: ", enemy_options)
                        target_label = None
                        for t, opt in zip(enemy_targets, enemy_options):
                            if opt == target:
                                target_label = t
                                break
                        print(f"{board[target_label].tclass} на клетке {target_label} заморожен на 1 ход!")
                        board[target_label].frozen = 1
                    else:
                        print("Нет доступных целей для заморозки.")
                elif "Хилл" in mage_choice:
                    if moving_token.cooldown == 0:
                        allies = [(cell, token) for cell, token in board.items() 
                                  if token is not None and token.side == current_turn and token.hp < token.max_hp]
                        if allies:
                            print("Доступные союзники для лечения (если не выбрать, лечится маг):")
                            ally_options = [f"{token.tclass} на клетке {cell} (H:{token.hp}/{token.max_hp})" for cell, token in allies]
                            ally_choice = choose_option("Выберите союзника для лечения: ", ally_options)
                            target_cell = None
                            for cell, token in allies:
                                option_str = f"{token.tclass} на клетке {cell} (H:{token.hp}/{token.max_hp})"
                                if option_str == ally_choice:
                                    target_cell = cell
                                    break
                            if target_cell:
                                print(f"{moving_token.tclass} лечит союзника на клетке {target_cell} на 2 HP.")
                                board[target_cell].hp = min(board[target_cell].hp + 2, board[target_cell].max_hp)
                            else:
                                print("Союзник не выбран. Лечится маг.")
                                moving_token.hp = min(moving_token.hp + 2, moving_token.max_hp)
                        else:
                            print("Нет союзников, нуждающихся в лечении. Лечится маг.")
                            moving_token.hp = min(moving_token.hp + 2, moving_token.max_hp)
                        moving_token.cooldown = 5
                    else:
                        print("Хилл недоступен.")
                if moving_token.cooldown is not None and moving_token.cooldown > 0:
                    moving_token.cooldown -= 1

        current_turn = 'R' if current_turn == 'B' else 'B'
        input("\nНажмите Enter для следующего хода...")
def update_freeze():
    for cell, token in board.items():
        if token is not None and token.frozen > 0:
            token.frozen -= 1

if __name__ == "__main__":
    main()