import os
import re
import math
import sys

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
        label = m.group(1)  # например, "1", "A", "M" и т.д.
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

# Класс токена с добавленным полем cooldown для Mage и Archer
class Token:
    def __init__(self, side, tclass, hp, attack, defense):
        self.side = side    # 'B' или 'R'
        self.tclass = tclass
        self.hp = hp
        self.attack = attack
        self.defense = defense  # Используем как значение щита
        if tclass in ["Mage", "Archer"]:
            self.cooldown = 0  # 0 означает способность готова
        else:
            self.cooldown = None
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
# Для клетки source объединяем:
# - прямых соседей (neighbors_map[source])
# - для каждого соседа добавляем его соседей (neighbors_map[nbr])
# - плюс саму исходную клетку
def extended_targets(source_label):
    ext = set(neighbors_map.get(source_label, []))
    for nbr in neighbors_map.get(source_label, []):
        ext.update(neighbors_map.get(nbr, []))
    ext.add(source_label)
    return list(ext)

# Функция для расширённой атаки (для Mage и Archer), которая выполняется только если cooldown == 0
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
    # Расширённая атака не даёт контратаку
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

def apply_damage(target, damage):
    """
    Применяет урон target по механике щита.
    Если damage <= target.defense, щит уменьшается на damage//2, и HP не меняются.
    Если damage > target.defense, щит сбрасывается, а остаток (damage - target.defense) вычитается из HP.
    Возвращает количество нанесённого урона по HP.
    """
    if damage <= target.defense:
        reduction = damage // 2
        target.defense -= reduction
        if target.defense < 0:
            target.defense = 0
        print(f"Щит цели уменьшен на {reduction} (новый щит: {target.defense}).")
        return 0
    else:
        remainder = damage - target.defense
        print(f"Щит цели ({target.defense}) пробит, остаток урона: {remainder}.")
        target.defense = 0
        target.hp -= remainder
        return remainder

# Модифицированная функция combat с разрушаемым щитом и корректной обработкой контратак:
def combat(attacker, defender, allow_counterattack=True):
    raw_dmg = attacker.attack - defender.defense
    if raw_dmg > 0:
        # Если атака пробивает щит, наносим весь урон напрямую в HP
        dmg = raw_dmg
        print(f"{attacker.tclass} наносит {dmg} урона {defender.tclass} (щит не учитывается).")
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
        # Если атака не пробивает щит, наносим половину атаки в виде повреждения щита
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
        # Если атака меньше текущего щита, то щит разрушается не полностью: уменьшается на половину атаки
        special_dmg = attacker.attack // 2
        print(f"{attacker.tclass} пробивает щит {defender.tclass} и наносит {special_dmg} повреждений щиту.")
        defender.defense -= special_dmg
        if defender.defense < 0:
            defender.defense = 0
        if allow_counterattack:
            counter = defender.attack // 2
            print(f"{defender.tclass} контратакует и наносит {counter} урона {attacker.tclass}.")
            attacker.hp -= counter
            if attacker.hp <= 0:
                print(f"{attacker.tclass} побеждён в контратаке!")
                return "attacker_dead"
        return "both_alive"

# Инициализация токенов согласно новой схеме
# Для команды Blue:
#   Soldier (самый сильный) на "3": HP=10, ATK=5, DEF=1
#   Mage на "4": HP=6, ATK=6, DEF=2 (способность: расширенная атака раз в 4 хода)
#   Knight на "C": HP=5, ATK=4, DEF=8
#   Archer на "2": HP=4, ATK=7, DEF=1
board["3"] = Token('B', "Soldier", 10, 5, 1)
board["4"] = Token('B', "Mage", 6, 6, 2)
board["C"] = Token('B', "Knight", 5, 4, 8)
board["2"] = Token('B', "Archer", 4, 7, 1)

# Для команды Red:
#   Soldier на "L": HP=10, ATK=5, DEF=1
#   Mage на "O": HP=6, ATK=6, DEF=2
#   Knight на "K": HP=5, ATK=4, DEF=8
#   Archer на "N": HP=4, ATK=7, DEF=1
board["L"] = Token('R', "Soldier", 10, 5, 1)
board["O"] = Token('R', "Mage", 6, 6, 2)
board["K"] = Token('R', "Knight", 5, 4, 8)
board["N"] = Token('R', "Archer", 4, 7, 1)

# Функция получения доступных клеток для перемещения для токена, согласно neighbors_map
def get_available_moves(cell_label):
    return [nbr for nbr in neighbors_map.get(cell_label, []) if board.get(nbr) is None]

# Основной игровой цикл с возможностью завершения игры
def main():
    current_turn = 'B'  # Blue начинают
    while True:
        print_board()
        blue_exists = any(token is not None and token.side == 'B' for token in board.values())
        red_exists = any(token is not None and token.side == 'R' for token in board.values())
        if not blue_exists or not red_exists:
            winner = 'B' if blue_exists else 'R'
            print(f"\nПобедили {'Синие' if winner=='B' else 'Красные'}!")
            break

        side_name = "Синие" if current_turn == 'B' else "Красные"
        print(f"\nХод {side_name}.")

        # Выбор токена текущего игрока
        available_tokens = [(cell, token) for cell, token in board.items() if token is not None and token.side == current_turn]
        if not available_tokens:
            print("Нет токенов для перемещения.")
            break
        print("\nВаши токены:")
        token_options = [f"{token.tclass} на клетке {cell} (H:{token.hp} A:{token.attack} D:{token.defense})" for cell, token in available_tokens]
        chosen = choose_option("Выберите номер токена для перемещения: ", token_options)
        chosen_cell = None
        moving_token = None
        for (cell, token), opt in zip(available_tokens, token_options):
            if opt == chosen:
                chosen_cell = cell
                moving_token = token
                break

        # Получаем доступные клетки для перемещения
        moves = get_available_moves(chosen_cell)
        if not moves:
            print("Нет доступных клеток для перемещения из этой клетки.")
            input("Нажмите Enter, чтобы продолжить...")
            continue
        print("\nДоступные клетки для перемещения:")
        move_options = [f"Клетка {cell}" for cell in moves]
        dest_choice = choose_option("Выберите клетку для перемещения: ", move_options)
        destination = None
        for cell, opt in zip(moves, move_options):
            if opt == dest_choice:
                destination = cell
                break

        board[chosen_cell] = None
        board[destination] = moving_token
        print(f"\n{moving_token.tclass} перемещён с клетки {chosen_cell} на клетку {destination}.")

        # Если токен Mage или Archer, проверяем способность расширённой атаки раз в 4 хода
        if moving_token.tclass in ["Mage", "Archer"]:
            if moving_token.cooldown == 0:
                print(f"\nСпециальная атака {moving_token.tclass} доступна (расширенный выстрел).")
                extended_attack(moving_token, destination, current_turn)
                moving_token.cooldown = 4  # сбрасываем способность, следующие 3 хода без расширённой атаки
            else:
                print(f"\nСпециальная атака недоступна, еще {moving_token.cooldown} ход(ов) до восстановления.")
                # Выполняем стандартную атаку для расширённых классов, как у остальных
                attackable = [cell for cell in neighbors_map.get(destination, []) if board.get(cell) is not None and board[cell].side != current_turn]
                if attackable:
                    print("\nДоступные клетки для атаки:")
                    enemy_options = [f"{board[cell].tclass} на клетке {cell} (H:{board[cell].hp} A:{board[cell].attack} D:{board[cell].defense})" for cell in attackable]
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
                moving_token.cooldown -= 1  # уменьшаем счётчик способности
        else:
            # Для остальных токенов: стандартная атака по соседям
            attackable = [cell for cell in neighbors_map.get(destination, []) if board.get(cell) is not None and board[cell].side != current_turn]
            if attackable:
                print("\nДоступные клетки для атаки:")
                enemy_options = [f"{board[cell].tclass} на клетке {cell} (H:{board[cell].hp} A:{board[cell].attack} D:{board[cell].defense})" for cell in attackable]
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

        current_turn = 'R' if current_turn == 'B' else 'B'
        input("\nНажмите Enter для следующего хода...")

if __name__ == "__main__":
    main()
