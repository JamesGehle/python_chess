import pygame
import sys
import time
import math

pygame.init()

# ----- WINDOW / LAYOUT -----

screen = pygame.display.set_mode((1000, 800))

BOARD_SIZE = 720
SQUARE_SIZE = BOARD_SIZE // 8
PANEL_WIDTH = 380
WIDTH = BOARD_SIZE + PANEL_WIDTH
HEIGHT = BOARD_SIZE

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Python Chess")


# ----- VISUAL THEME -----
"""
A darker application shell lets the board stand out while the
green palette keeps the interface visually cohesive
"""
LIGHT_SQUARE = (238, 229, 211)
DARK_SQUARE = (116, 145, 112)
LIGHT_ALT = (232, 222, 203)
DARK_ALT = (108, 136, 105)

BACKGROUND = (18, 22, 25)
PANEL = (27, 32, 36)
PANEL_2 = (34, 40, 44)
PANEL_3 = (45, 53, 58)
BORDER = (65, 74, 78)

TEXT = (242, 244, 245)
MUTED = (151, 162, 168)
ACCENT = (113, 184, 130)
ACCENT_BRIGHT = (151, 220, 166)
SELECTED = (244, 197, 66)
MOVE = (119, 205, 140)
CAPTURE = (221, 91, 91)
CHECK = (225, 76, 76)

WHITE_CLOCK = (239, 239, 234)
BLACK_CLOCK = (36, 40, 43)
CLOCK_DARK_TEXT = (25, 28, 30)


# ----- FONTS -----

piece_font = pygame.font.SysFont("dejavusans", 64)
small_font = pygame.font.SysFont("arial", 23)
button_font = pygame.font.SysFont("arial", 19)
history_font = pygame.font.SysFont("arial", 18)
title_font = pygame.font.SysFont("arial", 31, bold=True)
clock_font = pygame.font.SysFont("consolas", 30, bold=True)
status_font = pygame.font.SysFont("arial", 22, bold=True)


# ----- PIECES -----

PIECES = {
    "white": {
        "king": "♔",
        "queen": "♕",
        "rook": "♖",
        "bishop": "♗",
        "knight": "♘",
        "pawn": "♙"
    },
    "black": {
        "king": "♚",
        "queen": "♛",
        "rook": "♜",
        "bishop": "♝",
        "knight": "♞",
        "pawn": "♟"
    }
}

PIECE_LETTERS = {
    "king": "K",
    "queen": "Q",
    "rook": "R",
    "bishop": "B",
    "knight": "N",
    "pawn": ""
}

PROMOTION_CHOICES = ["queen", "rook", "bishop", "knight"]


# ----- GAME STATE -----

class Piece:
    """
    Represents one chess piece and the state that belongs to it.

    has_moved is required for rules such as castling and a pawn's
    initial two-square move. Keeping it with the piece prevents
    those rules from depending on unrelated global state.
    """
    def __init__(self, color, piece_type):
        self.color = color
        self.type = piece_type
        self.has_moved = False


def create_board():
    """
    Creates the standard starting chess position.

    Row 0 is Black's back rank and row 7 is White's back rank,
    which makes pawn movement directions consistent everywhere
    else in the program.
    """
    board = [[None for _ in range(8)] for _ in range(8)]

    back_row = [
        "rook", "knight", "bishop", "queen",
        "king", "bishop", "knight", "rook"
    ]

    for col in range(8):
        board[0][col] = Piece("black", back_row[col])
        board[1][col] = Piece("black", "pawn")
        board[6][col] = Piece("white", "pawn")
        board[7][col] = Piece("white", back_row[col])

    return board


board = create_board()
turn = "white"
selected = None
valid_moves = []
en_passant_target = None
game_over = False
game_message = ""
move_history = []
move_scroll = 0
last_seen_move_count = 0


# ----- ANIMATION STATE -----

"""
Animation is presentation-only. The actual board is updated before
the animation starts so rule calculations always use the new position.
"""
animation = None
ANIMATION_TIME = 300


# TIMER STATE

timer_enabled = False
timer_presets = [
    ("1 + 0", 60, 0),
    ("3 + 0", 180, 0),
    ("5 + 0", 300, 0),
    ("10 + 0", 600, 0),
    ("15 + 10", 900, 10),
    ("30 + 0", 1800, 0)
]
selected_preset = 3
time_limit = timer_presets[selected_preset][1]
increment_seconds = timer_presets[selected_preset][2]
white_time = time_limit
black_time = time_limit
last_timer_update = time.time()


# PROMOTION STATE

promotion_pending = None


def reset_timer():
    """
    Resets both clocks to the currently selected time control.

    The clock is kept independent from the board so changing or
    restarting a game can reset time without duplicating chess logic.
    """
    global white_time, black_time, last_timer_update

    white_time = time_limit
    black_time = time_limit
    last_timer_update = time.time()


def update_timer():
    """
    Advances the active player's clock using real elapsed time.

    Measuring elapsed time instead of subtracting a fixed amount
    every frame keeps the timer accurate even if rendering slows down.
    """
    global white_time, black_time, last_timer_update
    global game_over, game_message

    now = time.time()
    elapsed = now - last_timer_update
    last_timer_update = now

    if not timer_enabled or game_over or animation or promotion_pending:
        return

    if turn == "white":
        white_time = max(0, white_time - elapsed)

        if white_time <= 0:
            game_over = True
            game_message = "Time — Black wins!"
    else:
        black_time = max(0, black_time - elapsed)

        if black_time <= 0:
            game_over = True
            game_message = "Time — White wins!"


def format_time(seconds):
    """
    Converts seconds into a readable chess-clock display.

    Hours are automatically included for longer controls so the
    same function works for every preset without special UI code.
    """
    seconds = max(0, int(seconds))
    minutes = seconds // 60
    seconds %= 60

    if minutes >= 60:
        hours = minutes // 60
        minutes %= 60
        return f"{hours}:{minutes:02d}:{seconds:02d}"

    return f"{minutes}:{seconds:02d}"


def draw_board():
    """
    Draws the board and its current check warning.

    The check warning uses a translucent red overlay and inset border
    so the checked king is obvious without destroying the square's
    underlying color or piece visibility.
    """
    for row in range(8):
        for col in range(8):
            if (row + col) % 2 == 0:
                color = LIGHT_ALT if (row * 8 + col) % 4 == 0 else LIGHT_SQUARE
            else:
                color = DARK_ALT if (row * 8 + col) % 4 == 0 else DARK_SQUARE

            pygame.draw.rect(
                screen,
                color,
                (col * SQUARE_SIZE, row * SQUARE_SIZE,
                 SQUARE_SIZE, SQUARE_SIZE)
            )

    pygame.draw.rect(
        screen,
        BORDER,
        (0, 0, BOARD_SIZE, BOARD_SIZE),
        3
    )

    if not game_over and is_in_check(turn):
        king = find_king(turn)

        if king:
            row, col = king

            overlay = pygame.Surface(
                (SQUARE_SIZE, SQUARE_SIZE),
                pygame.SRCALPHA
            )
            overlay.fill((*CHECK, 100))
            screen.blit(
                overlay,
                (col * SQUARE_SIZE, row * SQUARE_SIZE)
            )

            pygame.draw.rect(
                screen,
                CHECK,
                (col * SQUARE_SIZE + 7, row * SQUARE_SIZE + 7,
                 SQUARE_SIZE - 14, SQUARE_SIZE - 14),
                6,
                border_radius=8
            )


def draw_highlights():
    """
    Shows the selected piece and all of its legal destinations.

    Empty destinations get small target dots while captures get
    rings, allowing the player to distinguish move types immediately.
    """
    if selected:
        row, col = selected

        overlay = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        overlay.fill((*SELECTED, 55))
        screen.blit(overlay, (col * SQUARE_SIZE, row * SQUARE_SIZE))

        pygame.draw.rect(
            screen,
            SELECTED,
            (col * SQUARE_SIZE + 5, row * SQUARE_SIZE + 5,
             SQUARE_SIZE - 10, SQUARE_SIZE - 10),
            4,
            border_radius=7
        )

        for move_row, move_col in valid_moves:
            center = (
                move_col * SQUARE_SIZE + SQUARE_SIZE // 2,
                move_row * SQUARE_SIZE + SQUARE_SIZE // 2
            )

            if board[move_row][move_col]:
                pygame.draw.circle(screen, CAPTURE, center, 28, 5)
                pygame.draw.circle(screen, (245, 245, 245), center, 32, 1)
            else:
                pygame.draw.circle(screen, MOVE, center, 10)
                pygame.draw.circle(screen, (245, 245, 245), center, 12, 1)


def draw_piece(piece, x, y, scale=1.0):
    """
    Renders a chess piece with a subtle shadow.

    The shadow separates Unicode glyphs from both light and dark
    squares, making the pieces look less like raw text without
    requiring external image files.
    """
    font_size = max(20, int(64 * scale))
    font = piece_font if scale == 1.0 else pygame.font.SysFont(
        "dejavusans", font_size
    )

    symbol = PIECES[piece.color][piece.type]
    text_color = (249, 249, 246) if piece.color == "white" else (24, 27, 29)

    shadow = font.render(symbol, True, (0, 0, 0))
    shadow.set_alpha(70)
    screen.blit(
        shadow,
        shadow.get_rect(center=(x + 3, y + 4))
    )

    text = font.render(symbol, True, text_color)
    screen.blit(text, text.get_rect(center=(x, y)))


def draw_pieces():
    """
    Draws all stationary pieces.

    The destination square of an active animation is skipped so the
    animated copy can be drawn separately on top of the board.
    """
    for row in range(8):
        for col in range(8):
            piece = board[row][col]

            if piece:
                if animation and animation["end"] == (row, col):
                    continue

                draw_piece(
                    piece,
                    col * SQUARE_SIZE + SQUARE_SIZE // 2,
                    row * SQUARE_SIZE + SQUARE_SIZE // 2 - 2
                )


def update_animation():
    """
    Draws a smoothly animated piece between its old and new squares.

    Quintic easing gives the movement a soft start and finish, while
    a small arc and scale change make the piece feel like it is being
    lifted and placed rather than simply translated by pixels.
    """
    global animation

    if animation is None:
        return

    elapsed = pygame.time.get_ticks() - animation["start_time"]
    progress = min(1.0, elapsed / animation["duration"])

    # More natural acceleration curve.
    eased = progress ** 3 * (
        progress * (progress * 6 - 15) + 10
    )

    sr, sc = animation["start"]
    er, ec = animation["end"]

    start_x = sc * SQUARE_SIZE + SQUARE_SIZE // 2
    start_y = sr * SQUARE_SIZE + SQUARE_SIZE // 2
    end_x = ec * SQUARE_SIZE + SQUARE_SIZE // 2
    end_y = er * SQUARE_SIZE + SQUARE_SIZE // 2

    x = start_x + (end_x - start_x) * eased
    y = start_y + (end_y - start_y) * eased

    # The sine arc peaks halfway through the movement and returns to zero.
    lift = 13 * math.sin(math.pi * progress)
    y -= lift

    scale = 1.0 + 0.05 * math.sin(math.pi * progress)

    draw_piece(animation["piece"], x, y, scale)

    if progress >= 1.0:
        animation = None


def draw_clock(x, y, color, seconds):
    """
    Draws one player's clock with an active-player indicator.

    The currently running side gets an accent border, making it clear
    which clock is counting down without needing extra labels.
    """
    active = timer_enabled and not game_over and turn == color

    background = WHITE_CLOCK if color == "white" else BLACK_CLOCK
    text_color = CLOCK_DARK_TEXT if color == "white" else TEXT

    pygame.draw.rect(
        screen,
        background,
        (x, y, 155, 62),
        border_radius=9
    )

    pygame.draw.rect(
        screen,
        ACCENT_BRIGHT if active else BORDER,
        (x, y, 155, 62),
        3 if active else 2,
        border_radius=9
    )

    text = clock_font.render(format_time(seconds), True, text_color)
    screen.blit(text, text.get_rect(center=(x + 77, y + 31)))


def draw_button(rect, label, active=False):
    """
    Draws a consistent rounded UI button.

    Centralizing button rendering keeps the settings panel visually
    consistent and makes active selections easy to identify.
    """
    pygame.draw.rect(
        screen,
        ACCENT if active else PANEL_3,
        rect,
        border_radius=7
    )

    pygame.draw.rect(
        screen,
        ACCENT_BRIGHT if active else BORDER,
        rect,
        2,
        border_radius=7
    )

    text = button_font.render(
        label,
        True,
        (20, 29, 23) if active else TEXT
    )
    screen.blit(text, text.get_rect(center=rect.center))


def draw_history():
    """
    Draws the right-side game panel and a scrollable move history.

    The move list automatically scrolls to the newest move whenever
    a new move is made, while still allowing manual scrolling.
    The visible log area ends above the status indicator and clocks.
    """
    global move_scroll, last_seen_move_count

    panel_x = BOARD_SIZE

    pygame.draw.rect(
        screen,
        PANEL,
        (panel_x, 0, PANEL_WIDTH, HEIGHT)
    )

    # Header
    title = title_font.render("Chess", True, TEXT)
    subtitle = history_font.render("GAME", True, MUTED)

    screen.blit(title, (panel_x + 22, 17))
    screen.blit(subtitle, (panel_x + 22, 52))

    table_x = panel_x + 16
    table_y = 84
    table_width = PANEL_WIDTH - 32

    pygame.draw.rect(
        screen,
        PANEL_2,
        (table_x, table_y, table_width, 34),
        border_radius=6
    )

    screen.blit(
        history_font.render("#", True, MUTED),
        (table_x + 10, table_y + 7)
    )
    screen.blit(
        history_font.render("White", True, MUTED),
        (table_x + 54, table_y + 7)
    )
    screen.blit(
        history_font.render("Black", True, MUTED),
        (table_x + 205, table_y + 7)
    )

    # ----- SCROLLABLE MOVE LOG -----

    row_height = 31
    log_top = table_y + 40

    if timer_enabled:
        # Leave room for the turn indicator and both clocks.
        log_bottom = HEIGHT - 304
    else:
        # Leave room for the turn indicator.
        log_bottom = HEIGHT - 235

    log_height = max(40, log_bottom - log_top)
    visible_rows = max(1, log_height // row_height)
    total_rows = (len(move_history) + 1) // 2
    max_scroll = max(0, total_rows - visible_rows)

    # Automatically scroll to the newest move whenever a move is added.
    if len(move_history) != last_seen_move_count:
        last_seen_move_count = len(move_history)
        move_scroll = max_scroll
    else:
        move_scroll = min(move_scroll, max_scroll)

    first_row = move_scroll
    last_row = min(total_rows, first_row + visible_rows)

    # Clip drawing to the move-log area so nothing can draw over the controls.
    old_clip = screen.get_clip()
    screen.set_clip(
        pygame.Rect(
            table_x,
            log_top,
            table_width,
            log_height
        )
    )

    for row_index in range(first_row, last_row):
        index = row_index * 2

        white_move = (
            move_history[index]
            if index < len(move_history)
            else ""
        )
        black_move = (
            move_history[index + 1]
            if index + 1 < len(move_history)
            else ""
        )

        y = log_top + (row_index - first_row) * row_height

        if row_index == (len(move_history) - 1) // 2:
            pygame.draw.rect(
                screen,
                (46, 67, 52),
                (table_x, y, table_width, row_height),
                border_radius=4
            )
        elif row_index % 2 == 0:
            pygame.draw.rect(
                screen,
                (30, 36, 40),
                (table_x, y, table_width, row_height)
            )

        screen.blit(
            history_font.render(str(row_index + 1), True, MUTED),
            (table_x + 10, y + 6)
        )
        screen.blit(
            history_font.render(white_move, True, TEXT),
            (table_x + 54, y + 6)
        )
        screen.blit(
            history_font.render(black_move, True, TEXT),
            (table_x + 205, y + 6)
        )

    screen.set_clip(old_clip)

    # Scrollbar
    if total_rows > visible_rows:
        scrollbar_x = table_x + table_width - 7
        scrollbar_height = max(25, int(log_height * visible_rows / total_rows))
        scrollbar_range = log_height - scrollbar_height

        scrollbar_y = log_top
        if max_scroll > 0:
            scrollbar_y += int(
                scrollbar_range * move_scroll / max_scroll
            )

        pygame.draw.rect(
            screen,
            BORDER,
            (scrollbar_x, log_top, 5, log_height),
            border_radius=3
        )
        pygame.draw.rect(
            screen,
            MUTED,
            (scrollbar_x, scrollbar_y, 5, scrollbar_height),
            border_radius=3
        )

    # ----- CLOCKS -----

    if timer_enabled:
        draw_clock(panel_x + 20, HEIGHT - 254, "white", white_time)
        draw_clock(panel_x + 200, HEIGHT - 254, "black", black_time)

    # ----- TIME CONTROL PRESETS -----

    label = history_font.render("TIME CONTROL", True, MUTED)
    screen.blit(label, (panel_x + 20, HEIGHT - 181))

    for i, (name, _, _) in enumerate(timer_presets):
        x = panel_x + 20 + (i % 3) * 108
        y = HEIGHT - 158 + (i // 3) * 37

        draw_button(
            pygame.Rect(x, y, 98, 30),
            name,
            active=(i == selected_preset)
        )

    # ----- BOTTOM CONTROLS -----

    draw_button(
        pygame.Rect(panel_x + 20, HEIGHT - 76, 150, 40),
        "Timer ON" if timer_enabled else "Timer OFF",
        active=timer_enabled
    )

    draw_button(
        pygame.Rect(panel_x + 190, HEIGHT - 76, 150, 40),
        "New Game"
    )


def draw_status():
    """
    Draws a compact status pill over the lower-left of the board.

    Check receives a strong red treatment, while normal turn information
    stays quieter so it does not compete with the actual chess position.
    """
    if game_over:
        label = game_message
        color = CHECK if "wins" in game_message else SELECTED
    elif is_in_check(turn):
        label = f"{turn.upper()} IS IN CHECK"
        color = CHECK
    else:
        label = f"{turn.capitalize()}'s turn"
        color = TEXT

    text = status_font.render(label, True, color)

    # Keep the turn indicator in the control panel, directly above
    # the time-control section instead of covering the board.
    status_x = BOARD_SIZE + 20

    if timer_enabled:
        status_y = HEIGHT - 294
    else:
        status_y = HEIGHT - 218

    rect = text.get_rect(topleft=(status_x, status_y))

    background = pygame.Surface(
        (rect.width + 28, rect.height + 14),
        pygame.SRCALPHA
    )
    background.fill((15, 19, 21, 225))
    screen.blit(background, (rect.x - 14, rect.y - 7))

    pygame.draw.rect(
        screen,
        color,
        (
            rect.x - 14,
            rect.y - 7,
            rect.width + 28,
            rect.height + 14
        ),
        2,
        border_radius=8
    )

    screen.blit(text, rect)


def draw_promotion_menu():
    """
    Displays the mandatory pawn-promotion selection dialog.

    The board is dimmed while the four legal promotion pieces are
    presented as large clickable choices, preventing accidental input
    from being interpreted as another chess move.
    """
    if promotion_pending is None:
        return

    overlay = pygame.Surface(
        (BOARD_SIZE, BOARD_SIZE),
        pygame.SRCALPHA
    )
    overlay.fill((0, 0, 0, 155))
    screen.blit(overlay, (0, 0))

    box = pygame.Rect(100, 245, 520, 230)

    pygame.draw.rect(screen, PANEL, box, border_radius=14)
    pygame.draw.rect(screen, BORDER, box, 2, border_radius=14)

    title = title_font.render("Choose promotion", True, TEXT)
    screen.blit(title, title.get_rect(center=(BOARD_SIZE // 2, box.y + 35)))

    color = promotion_pending["color"]

    for i, piece_type in enumerate(PROMOTION_CHOICES):
        button = pygame.Rect(
            box.x + 24 + i * 122,
            box.y + 72,
            104,
            120
        )

        draw_button(button, "", active=False)

        draw_piece(
            Piece(color, piece_type),
            button.centerx,
            button.y + 45
        )

        label = button_font.render(
            piece_type.capitalize(),
            True,
            TEXT
        )
        screen.blit(
            label,
            label.get_rect(center=(button.centerx, button.bottom - 20))
        )


def in_bounds(row, col):
    """
    Tests whether a board coordinate lies inside the 8x8 board.

    Centralizing this check prevents movement code from accidentally
    indexing outside the board while examining possible destinations.
    """
    return 0 <= row < 8 and 0 <= col < 8


def find_king(color):
    """
    Locates the king belonging to a particular side.

    King position is searched dynamically because it changes whenever
    the king moves and is also needed repeatedly during move simulation.
    """
    for row in range(8):
        for col in range(8):
            piece = board[row][col]

            if piece and piece.color == color and piece.type == "king":
                return row, col

    return None


def opposite(color):
    """
    Returns the opponent's color.

    Keeping this tiny rule in one helper makes turn switching and attack
    calculations less repetitive and less error-prone.
    """
    return "black" if color == "white" else "white"


def square_attacked(row, col, attacking_color):
    """
    Determines whether a square is attacked by a particular side.

    This intentionally checks attacks directly rather than calling
    legal-move generation, because king-safety calculations must still
    work for pieces that are pinned to their own king.
    """
    pawn_direction = -1 if attacking_color == "white" else 1

    for dc in (-1, 1):
        pawn_row = row - pawn_direction
        pawn_col = col - dc

        if in_bounds(pawn_row, pawn_col):
            piece = board[pawn_row][pawn_col]

            if (
                piece
                and piece.color == attacking_color
                and piece.type == "pawn"
            ):
                return True

    knight_moves = [
        (-2, -1), (-2, 1), (-1, -2), (-1, 2),
        (1, -2), (1, 2), (2, -1), (2, 1)
    ]

    for dr, dc in knight_moves:
        r = row + dr
        c = col + dc

        if in_bounds(r, c):
            piece = board[r][c]

            if (
                piece
                and piece.color == attacking_color
                and piece.type == "knight"
            ):
                return True

    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue

            r = row + dr
            c = col + dc

            if in_bounds(r, c):
                piece = board[r][c]

                if (
                    piece
                    and piece.color == attacking_color
                    and piece.type == "king"
                ):
                    return True

    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        r = row + dr
        c = col + dc

        while in_bounds(r, c):
            piece = board[r][c]

            if piece:
                if piece.color == attacking_color:
                    if piece.type in ("rook", "queen"):
                        return True
                break

            r += dr
            c += dc

    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        r = row + dr
        c = col + dc

        while in_bounds(r, c):
            piece = board[r][c]

            if piece:
                if piece.color == attacking_color:
                    if piece.type in ("bishop", "queen"):
                        return True
                break

            r += dr
            c += dc

    return False


def is_in_check(color):
    """
    Tests whether the specified side's king is currently attacked.

    A missing king is considered unsafe during simulated positions,
    which prevents illegal hypothetical moves from passing validation.
    """
    king = find_king(color)

    if king is None:
        return True

    return square_attacked(
        king[0],
        king[1],
        opposite(color)
    )


def get_sliding_moves(row, col, color, directions):
    """
    Generates moves for sliding pieces along a set of directions.

    A ray stops at the first occupied square because bishops, rooks,
    and queens cannot jump through other pieces.
    """
    moves = []

    for dr, dc in directions:
        r = row + dr
        c = col + dc

        while in_bounds(r, c):
            target = board[r][c]

            if target is None:
                moves.append((r, c))
            else:
                if target.color != color:
                    moves.append((r, c))
                break

            r += dr
            c += dc

    return moves


def get_pseudo_moves(row, col):
    """
    Generates movement-rule-valid destinations without checking king safety.

    Keeping this separate from legal-move validation allows the same
    movement rules to be reused while simulated positions are tested.
    """
    piece = board[row][col]

    if piece is None:
        return []

    moves = []

    if piece.type == "pawn":
        direction = -1 if piece.color == "white" else 1
        new_row = row + direction

        if in_bounds(new_row, col) and board[new_row][col] is None:
            moves.append((new_row, col))

            start_row = 6 if piece.color == "white" else 1
            double_row = row + direction * 2

            if (
                row == start_row
                and in_bounds(double_row, col)
                and board[double_row][col] is None
            ):
                moves.append((double_row, col))

        for dc in (-1, 1):
            new_col = col + dc

            if in_bounds(new_row, new_col):
                target = board[new_row][new_col]

                if target and target.color != piece.color:
                    moves.append((new_row, new_col))

        if en_passant_target:
            target_row, target_col = en_passant_target

            if (
                new_row == target_row
                and abs(target_col - col) == 1
            ):
                moves.append((target_row, target_col))

    elif piece.type == "knight":
        for dr, dc in [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]:
            r = row + dr
            c = col + dc

            if in_bounds(r, c):
                target = board[r][c]

                if target is None or target.color != piece.color:
                    moves.append((r, c))

    elif piece.type == "bishop":
        moves += get_sliding_moves(
            row, col, piece.color,
            [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        )

    elif piece.type == "rook":
        moves += get_sliding_moves(
            row, col, piece.color,
            [(-1, 0), (1, 0), (0, -1), (0, 1)]
        )

    elif piece.type == "queen":
        moves += get_sliding_moves(
            row, col, piece.color,
            [
                (-1, -1), (-1, 1), (1, -1), (1, 1),
                (-1, 0), (1, 0), (0, -1), (0, 1)
            ]
        )

    elif piece.type == "king":
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue

                r = row + dr
                c = col + dc

                if in_bounds(r, c):
                    target = board[r][c]

                    if target is None or target.color != piece.color:
                        moves.append((r, c))

        # The king cannot castle through or into an attacked square.
        if not piece.has_moved and not is_in_check(piece.color):
            rook = board[row][7]

            if (
                rook
                and rook.type == "rook"
                and rook.color == piece.color
                and not rook.has_moved
                and board[row][5] is None
                and board[row][6] is None
                and not square_attacked(row, 5, opposite(piece.color))
                and not square_attacked(row, 6, opposite(piece.color))
            ):
                moves.append((row, 6))

            rook = board[row][0]

            if (
                rook
                and rook.type == "rook"
                and rook.color == piece.color
                and not rook.has_moved
                and board[row][1] is None
                and board[row][2] is None
                and board[row][3] is None
                and not square_attacked(row, 3, opposite(piece.color))
                and not square_attacked(row, 2, opposite(piece.color))
            ):
                moves.append((row, 2))

    return moves


def copy_board():
    """
    Creates an independent copy of the current board.

    Piece objects are copied as well because simulated moves must be
    able to alter has_moved without changing the actual game position.
    """
    new_board = [[None for _ in range(8)] for _ in range(8)]

    for row in range(8):
        for col in range(8):
            piece = board[row][col]

            if piece:
                copied = Piece(piece.color, piece.type)
                copied.has_moved = piece.has_moved
                new_board[row][col] = copied

    return new_board


def simulate_move(start, end):
    """
    Temporarily applies a move to test whether it exposes the king.

    Special handling for en passant and castling is required because
    both change more than just the start and destination squares.
    """
    global board

    old_board = board
    board = copy_board()

    sr, sc = start
    er, ec = end
    piece = board[sr][sc]

    if (
        piece.type == "pawn"
        and sc != ec
        and board[er][ec] is None
    ):
        board[sr][ec] = None

    board[er][ec] = piece
    board[sr][sc] = None

    if piece.type == "king" and abs(ec - sc) == 2:
        if ec == 6:
            rook = board[er][7]
            board[er][5] = rook
            board[er][7] = None
        else:
            rook = board[er][0]
            board[er][3] = rook
            board[er][0] = None

    unsafe = is_in_check(piece.color)
    board = old_board

    return unsafe


def get_legal_moves(row, col):
    """
    Filters movement-rule-valid moves through king-safety validation.

    This catches pins, discovered attacks, illegal king moves, and all
    other cases where a piece's normal movement would expose its king.
    """
    piece = board[row][col]

    if piece is None:
        return []

    legal = []

    for move in get_pseudo_moves(row, col):
        if not simulate_move((row, col), move):
            legal.append(move)

    return legal


def square_name(row, col):
    """
    Converts an internal board coordinate into algebraic chess notation.

    The board's row numbering runs from 0 at rank 8 to 7 at rank 1,
    so the rank must be inverted when producing the displayed name.
    """
    return "abcdefgh"[col] + str(8 - row)


def make_move(start, end):
    """
    Applies a legal move and starts its visual animation.

    Castling, en passant, promotion, the en-passant target, move
    notation, and the next player's turn are all coordinated here.
    """
    global en_passant_target, animation, promotion_pending
    global turn

    sr, sc = start
    er, ec = end

    piece = board[sr][sc]
    captured = board[er][ec]

    was_en_passant = (
        piece.type == "pawn"
        and sc != ec
        and captured is None
    )

    notation = PIECE_LETTERS[piece.type]

    if captured or was_en_passant:
        if piece.type == "pawn":
            notation += "abcdefgh"[sc]
        notation += "x"

    notation += square_name(er, ec)

    if was_en_passant:
        board[sr][ec] = None

    board[er][ec] = piece
    board[sr][sc] = None
    piece.has_moved = True

    if piece.type == "king" and abs(ec - sc) == 2:
        if ec == 6:
            rook = board[er][7]
            board[er][5] = rook
            board[er][7] = None
            rook.has_moved = True
            notation = "O-O"
        else:
            rook = board[er][0]
            board[er][3] = rook
            board[er][0] = None
            rook.has_moved = True
            notation = "O-O-O"

    en_passant_target = None

    if piece.type == "pawn" and abs(er - sr) == 2:
        en_passant_target = ((sr + er) // 2, sc)

    animation = {
        "piece": piece,
        "start": start,
        "end": end,
        "start_time": pygame.time.get_ticks(),
        "duration": ANIMATION_TIME
    }

    if piece.type == "pawn" and er in (0, 7):
        promotion_pending = {
            "row": er,
            "col": ec,
            "color": piece.color,
            "notation": notation
        }
        return

    finish_move(notation)


def finish_move(notation):
    """
    Finishes move bookkeeping after a normal move or promotion.

    The clock increment is awarded to the player who just moved before
    the turn changes, matching the standard interpretation of increment.
    """
    global turn, last_timer_update

    move_history.append(notation)

    mover = turn

    if timer_enabled and increment_seconds:
        if mover == "white":
            white_time_increment()
        else:
            black_time_increment()

    turn = opposite(turn)
    last_timer_update = time.time()
    check_game_state()


def white_time_increment():
    """
    Adds the configured increment to White's remaining clock.

    Keeping clock mutation in small dedicated functions makes the
    increment logic explicit instead of hiding it inside turn handling.
    """
    global white_time
    white_time += increment_seconds


def black_time_increment():
    """
    Adds the configured increment to Black's remaining clock.

    This mirrors White's increment function so both clock updates
    remain easy to locate and modify independently.
    """
    global black_time
    black_time += increment_seconds


def choose_promotion(piece_type):
    """
    Replaces a pawn with the player's selected promotion piece.

    Promotion is completed before the move is recorded, ensuring the
    board state and the displayed notation always describe the same move.
    """
    global promotion_pending

    if promotion_pending is None:
        return

    row = promotion_pending["row"]
    col = promotion_pending["col"]
    color = promotion_pending["color"]
    notation = promotion_pending["notation"]

    board[row][col] = Piece(color, piece_type)
    board[row][col].has_moved = True

    notation += "=" + PIECE_LETTERS[piece_type]
    promotion_pending = None

    finish_move(notation)


def has_legal_moves(color):
    """
    Checks whether a side has at least one legal move available.

    The first legal move ends the search immediately, which is enough
    to distinguish positions with no moves from positions that can continue.
    """
    for row in range(8):
        for col in range(8):
            piece = board[row][col]

            if piece and piece.color == color:
                if get_legal_moves(row, col):
                    return True

    return False


def check_game_state():
    """
    Determines check, checkmate, or stalemate after every completed move.

    A side with no legal moves is checkmated if its king is attacked;
    otherwise the exact same lack of moves is a stalemate draw.
    """
    global game_over, game_message

    if not has_legal_moves(turn):
        game_over = True

        if is_in_check(turn):
            game_message = f"Checkmate — {opposite(turn).capitalize()} wins!"
        else:
            game_message = "Stalemate — Draw!"
    elif is_in_check(turn):
        game_message = f"{turn.upper()} IS IN CHECK"
    else:
        game_message = ""


def restart_game():
    """
    Resets the complete game state to the standard starting position.

    Board state, move history, timers, selection, animation, promotion,
    and game-ending messages are all reset together to avoid stale state.
    """
    global board, turn, selected, valid_moves
    global en_passant_target, game_over, game_message
    global move_history, animation, promotion_pending
    global move_scroll, last_seen_move_count

    board = create_board()
    turn = "white"
    selected = None
    valid_moves = []
    en_passant_target = None
    game_over = False
    game_message = ""
    move_history = []
    move_scroll = 0
    last_seen_move_count = 0
    animation = None
    promotion_pending = None

    reset_timer()


def toggle_timer():
    """
    Enables or disables the selected chess clock.

    Disabling the timer leaves the board untouched; enabling it simply
    begins counting from the currently selected time control.
    """
    global timer_enabled, last_timer_update

    timer_enabled = not timer_enabled
    last_timer_update = time.time()


def select_timer_preset(index):
    """
    Changes the active time control and immediately resets both clocks.

    Each preset stores both its base time and increment, allowing the
    same selector to support controls such as 15 + 10 as well as 10 + 0.
    """
    global selected_preset, time_limit, increment_seconds

    selected_preset = index
    _, time_limit, increment_seconds = timer_presets[index]
    reset_timer()


def handle_promotion_click(pos):
    """
    Converts a click in the promotion dialog into a promotion choice.

    Clicks outside the four choices are ignored because promotion is
    mandatory and should not be cancellable by clicking the board.
    """
    if promotion_pending is None:
        return

    x, y = pos
    box = pygame.Rect(100, 245, 520, 230)

    for i, piece_type in enumerate(PROMOTION_CHOICES):
        button = pygame.Rect(
            box.x + 24 + i * 122,
            box.y + 72,
            104,
            120
        )

        if button.collidepoint(x, y):
            choose_promotion(piece_type)
            return


def handle_click(pos):
    """
    Handles board input, timer controls, and game-reset controls.

    Modal promotion input and move animations are given priority so
    clicks cannot accidentally perform multiple state changes at once.
    """
    global selected, valid_moves

    x, y = pos

    if promotion_pending:
        handle_promotion_click(pos)
        return

    if animation:
        return

    if x >= BOARD_SIZE:
        panel_x = BOARD_SIZE

        for i, _ in enumerate(timer_presets):
            button_x = panel_x + 20 + (i % 3) * 108
            button_y = HEIGHT - 158 + (i // 3) * 37
            button = pygame.Rect(button_x, button_y, 98, 30)

            if button.collidepoint(x, y):
                select_timer_preset(i)
                return

        if pygame.Rect(
            panel_x + 20, HEIGHT - 76, 150, 40
        ).collidepoint(x, y):
            toggle_timer()
            return

        if pygame.Rect(
            panel_x + 190, HEIGHT - 76, 150, 40
        ).collidepoint(x, y):
            restart_game()
            return

        return

    if game_over:
        return

    col = x // SQUARE_SIZE
    row = y // SQUARE_SIZE

    if selected is None:
        piece = board[row][col]

        if piece and piece.color == turn:
            selected = (row, col)
            valid_moves = get_legal_moves(row, col)

    elif (row, col) in valid_moves:
        make_move(selected, (row, col))
        selected = None
        valid_moves = []

    else:
        piece = board[row][col]

        if piece and piece.color == turn:
            selected = (row, col)
            valid_moves = get_legal_moves(row, col)
        else:
            selected = None
            valid_moves = []


# ----- MAIN LOOP -----

clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            handle_click(event.pos)

        if event.type == pygame.MOUSEWHEEL:
            if event.y != 0:
                move_scroll -= event.y * 2
                move_scroll = max(0, move_scroll)

    update_timer()

    screen.fill(BACKGROUND)

    draw_board()
    draw_highlights()
    draw_pieces()
    draw_history()
    draw_status()

    # Drawing the animated piece last makes it visually sit above the
    # stationary board pieces while it travels to its destination.
    if animation:
        update_animation()

    draw_promotion_menu()

    pygame.display.flip()
    clock.tick(60)
