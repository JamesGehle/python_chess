Python Chess

A fully playable chess game written in Python using Pygame.

The program implements the core rules and systems of chess, including:

Standard piece movement
Captures
Check
Checkmate
Stalemate
Pins
Discovered attacks
Castling
En passant
Pawn promotion
Legal-move filtering
Move history
Basic chess notation
Optional chess clocks
Multiple time controls
Move animations
Visual move indicators
Check highlighting
Promotion selection UI
Game restarting
Requirements

The program requires:

Python 3
Pygame

The pieces are rendered using Unicode chess symbols, so no external piece-image files are required.

The game initializes Pygame and creates a 1100 × 720 window. The chessboard occupies 720 × 720 pixels, making each square 90 × 90 pixels.

Board Representation

The chessboard is represented as an 8×8 Python list:

board = [[None for _ in range(8)] for _ in range(8)]

Each element is either:

None
A Piece object

The board is indexed as:

board[row][column]

Rows and columns range from 0 through 7.

Board Orientation
row 0 = Black's back rank
row 1 = Black's pawns
row 2
row 3
row 4
row 5
row 6 = White's pawns
row 7 = White's back rank

Columns correspond to:

0 = a
1 = b
2 = c
3 = d
4 = e
5 = f
6 = g
7 = h

Therefore:

board[7][4]

is White's starting king square, e1, while:

board[0][4]

is Black's starting king square, e8.

This coordinate system also makes pawn movement straightforward:

White moves toward decreasing row numbers.
Black moves toward increasing row numbers.
Piece Representation

Every chess piece is represented by a Piece object:

class Piece:
    def __init__(self, color, piece_type):
        self.color = color
        self.type = piece_type
        self.has_moved = False

Each piece stores:

color
type
has_moved

For example:

Piece("white", "rook")

represents a white rook.

The has_moved property is important because some chess rules depend on whether a piece has moved previously. It is used for:

Castling
A pawn's initial two-square move
Game State

Several global variables represent the current game:

board
turn
selected
valid_moves
en_passant_target
game_over
game_message
move_history
animation
promotion_pending

The timer system additionally uses:

timer_enabled
timer_presets
selected_preset
time_limit
increment_seconds
white_time
black_time
last_timer_update

The actual board is the authoritative source of the chess position. Animation and interface state do not replace or temporarily alter the authoritative position.

Movement System

Movement is handled in three major stages:

get_pseudo_moves()
get_legal_moves()
simulate_move()

The basic process is:

Player selects a piece
        ↓
Generate pseudo-legal moves
        ↓
Simulate each move
        ↓
Check whether own king is attacked
        ↓
Remove moves that expose the king
        ↓
Return legal moves

This separation allows the program to distinguish between:

"Can this piece move according to its normal movement rules?"

and:

"Can this piece make this move without leaving its own king in check?"

Pseudo-Legal Moves

A pseudo-legal move follows the movement rules of the piece but has not yet been checked for king safety.

For example:

White King ─ White Rook ───────── Black Rook

The white rook may have many movement possibilities according to normal rook movement.

However, if moving it exposes the white king to the black rook, those moves are illegal.

get_pseudo_moves() does not check this situation. It only determines whether the piece can physically move to each destination according to its movement rules.

King safety is handled afterward by get_legal_moves() and simulate_move().

Sliding Pieces

Bishops, rooks, and queens are sliding pieces because they can travel multiple squares in a direction.

The shared function:

get_sliding_moves()

handles their ray-based movement.

It receives a list of directions.

Rook Directions
[
    (-1, 0),
    (1, 0),
    (0, -1),
    (0, 1)
]

These represent:

up
down
left
right
Bishop Directions
[
    (-1, -1),
    (-1, 1),
    (1, -1),
    (1, 1)
]

These represent the four diagonals.

Queen

The queen uses all eight directions.

Sliding Algorithm

The algorithm starts one square away:

r = row + dr
c = col + dc

It repeatedly examines the next square.

If the square is empty:

moves.append((r, c))

and the piece continues along the ray.

If a piece is encountered:

An enemy piece can be captured.
A friendly piece cannot be entered.

Either way, the ray stops immediately.

This prevents sliding pieces from jumping over other pieces.

For example:

R . . . P . . .

The rook can travel through the empty squares but cannot travel through the pawn.

Pawns

Pawns are handled separately because their movement is asymmetric.

White moves:

row - 1

Black moves:

row + 1

A pawn can move forward if its destination is empty.

A pawn on its starting rank can move two squares if both squares are empty.

Starting rows:

White = 6
Black = 1

Pawns capture diagonally rather than moving diagonally normally.

The program checks both diagonal directions:

for dc in (-1, 1):

and allows a normal capture when an opposing piece occupies the target square.

En passant is also checked during pawn move generation.

Knights

Knights do not care about pieces between their starting and destination squares because they jump.

The eight possible offsets are:

(-2, -1)
(-2,  1)
(-1, -2)
(-1,  2)
( 1, -2)
( 1,  2)
( 2, -1)
( 2,  1)

For each destination, the program checks:

Whether it is on the board.
Whether it is empty or occupied by an enemy.

There is no path-clearance requirement for knights.

Kings

Kings can move one square in any direction.

The program checks:

dr in (-1, 0, 1)
dc in (-1, 0, 1)

except:

dr == 0 and dc == 0

which would represent staying in place.

King movement is later filtered through the normal legal-move system, so a king cannot move onto an attacked square.

Kings also receive special handling for castling.

Attack Detection

One of the most important functions is:

square_attacked(row, col, attacking_color)

It answers:

"Is this square attacked by the specified side?"

Attack detection is intentionally separate from normal legal-move generation.

This distinction is important because an attacked square is not always equivalent to a square a piece could legally move to.

Why Attack Detection Is Separate

The program does not determine attacks simply by calling:

get_legal_moves()

That would cause problems with pinned pieces.

For example:

Black Rook
    │
    │
White Piece
    │
White King

The white piece may be pinned and therefore unable to legally move.

However, the piece still matters when determining whether certain squares are attacked.

Therefore, square_attacked() examines the actual movement and attack geometry directly rather than asking whether the attacking piece has a legal move.

square_attacked()

The function checks each type of attack separately.

Pawn Attacks

The program determines the attacking pawn's direction:

White pawns attack toward decreasing rows.
Black pawns attack toward increasing rows.

The two diagonally adjacent pawn positions are examined.

If an attacking pawn occupies one of them, the target square is attacked.

Knight Attacks

The same eight offsets used for knight movement are checked.

If a knight belonging to the attacking side occupies one of those positions, the square is attacked.

King Attacks

The eight neighboring squares are checked.

If the attacking side's king occupies one, the square is considered attacked.

This is particularly important for:

King movement
Castling
Rook and Queen Attacks

The program traces four straight-line directions:

up
down
left
right

It continues until a piece is encountered.

If the first piece encountered belongs to the attacking side and is a:

rook

or:

queen

the square is attacked.

Any blocking piece immediately ends that ray.

Bishop and Queen Attacks

The same process is repeated for the four diagonal directions.

If the first encountered attacking piece is a:

bishop

or:

queen

the square is attacked.

This complete attack-detection system is implemented in square_attacked().

Check Detection

Check detection is simple once attack detection exists.

The function:

is_in_check(color)

does three main things.

1. Find the King

It calls:

find_king(color)

which scans the board until it finds that side's king.

2. Find the Opponent

It calls:

opposite(color)

which converts:

white → black
black → white
3. Check the King's Square

It effectively calls:

square_attacked(
    king_row,
    king_col,
    opposite(color)
)

If the result is True, the king is in check.

If a king cannot be found during a simulated position, that position is treated as unsafe.

Pins

There is no dedicated:

is_pinned()

function.

Pins are detected indirectly through move simulation.

Consider:

White King
    │
White Rook
    │
Black Rook

The white rook is pinned.

Normally, it could move sideways. But moving sideways would expose the white king to the black rook.

The program handles this without explicitly identifying the rook as pinned.

It:

Generates the rook's pseudo-legal moves.
Simulates each candidate move.
Checks whether the king is now in check.
Rejects moves that expose the king.

The process is:

Pseudo-legal move
        ↓
Move rook temporarily
        ↓
Check White's king
        ↓
King is attacked
        ↓
Move rejected

Therefore, no dedicated pin-detection algorithm is required.

Discovered Attacks

The same mechanism handles discovered attacks and discovered checks.

For example:

White King
    │
White Bishop
    │
Black Rook

If the bishop moves away, the rook's line toward the king becomes open.

The program does not need to explicitly recognize this as a "discovered attack."

Instead:

Generate the bishop's pseudo-legal move.
Simulate it.
Check the king.
Detect that the rook now attacks the king.
Reject the move.

Pins, discovered attacks, and similar tactical restrictions therefore emerge naturally from the general king-safety system.

Legal Move Generation

The central legal-move function is:

get_legal_moves(row, col)

Its basic process is:

for move in get_pseudo_moves(row, col):
    if not simulate_move((row, col), move):
        legal.append(move)

In plain English:

Generate every move the piece could make, simulate each one, and keep only the moves that do not leave its own king in check.

This is the core rule-validation mechanism.

Move Simulation

simulate_move() temporarily creates a copy of the board.

First:

old_board = board
board = copy_board()

The original position is saved and the copied position is modified as though the move happened.

The program then checks:

unsafe = is_in_check(piece.color)
board = old_board

The real board is restored afterward.

The function returns:

True

if the move leaves the moving side's king in check.

Otherwise it returns:

False

Therefore:

simulate_move(...) == True

means:

Illegal because the king would be unsafe.

While:

simulate_move(...) == False

means:

The move passes king-safety testing.

Why Simulation Is Powerful

The simulation system avoids requiring separate algorithms for every tactical restriction.

It automatically handles:

Absolute pins
Discovered checks
Illegal king moves
Blocking pieces that cannot legally move
Moving a pinned piece
Capturing a checking piece
Blocking a checking line
Castling through unsafe positions
En passant positions that expose the king

The fundamental rule is:

After your move, your king must not be attacked.

The program directly tests that rule.

Castling

Castling is implemented during king pseudo-move generation.

For castling to be considered, the king must:

not piece.has_moved

The corresponding rook must also:

not rook.has_moved

The squares between the king and rook must be empty.

The king additionally:

Cannot currently be in check.
Cannot pass through an attacked square.
Cannot finish on an attacked square.
Kingside Castling

The relevant squares are:

f1 / f8
g1 / g8

The king finishes on the:

g-file
Queenside Castling

The relevant squares are:

d1 / d8
c1 / c8

The king finishes on the:

c-file

When the move is actually executed, the rook is automatically moved as well.

En Passant

The program tracks:

en_passant_target

This records the square that can potentially be used for an en passant capture.

When a pawn moves two squares:

if piece.type == "pawn" and abs(er - sr) == 2:

the program sets the target to the square halfway between the starting and ending positions.

For example:

White pawn: e2 → e4

creates:

en passant target = e3

A neighboring enemy pawn can then potentially move diagonally into that target square.

When the move is executed, the captured pawn is removed from its original square:

board[sr][ec] = None

This is necessary because en passant captures a pawn that is not located on the destination square.

The simulation system also handles this special capture so that en passant cannot expose the moving player's king.

Pawn Promotion

When a pawn reaches the opposite end:

if piece.type == "pawn" and er in (0, 7):

the move is not immediately completed.

Instead, the program creates:

promotion_pending

This pauses normal chess input and displays the promotion selection interface.

The player can select:

Queen
Rook
Bishop
Knight

The pawn is replaced by a new Piece object.

Promotion notation is added as:

=Q
=R
=B
=N

Promotion is mandatory. Clicking outside the promotion choices does not cancel it.

Checkmate

Checkmate is detected after every completed move by:

check_game_state()

The program first asks:

has_legal_moves(turn)

If the current player has at least one legal move, play continues.

If the player has no legal moves, the program checks:

is_in_check(turn)

If both are true:

No legal moves
+
King in check
=
Checkmate

The game message becomes either:

Checkmate — White wins!

or:

Checkmate — Black wins!

depending on whose turn it was.

Stalemate

Stalemate uses almost the same detection system.

The difference is whether the king is in check:

No legal moves + King in check
        ↓
Checkmate

No legal moves + King NOT in check
        ↓
Stalemate

Therefore, no complicated separate stalemate algorithm is necessary.

The result becomes:

Stalemate — Draw!
Making a Move

Once a player clicks a legal destination, make_move() performs the actual move.

It coordinates:

Captures
En passant
Board updates
has_moved
Castling
En passant target
Animation
Promotion
Move notation
Turn progression

The board is updated before animation begins.

This is important because the animation is purely visual and does not represent authoritative game state.

The rules engine therefore always operates on the final position instead of an intermediate animation position.

Move Notation

The program maintains:

move_history

Each completed move is added to the list.

Piece letters are:

King   K
Queen  Q
Rook   R
Bishop B
Knight N
Pawn   ""

Captures use:

x

For pawn captures, the starting file is included.

For example:

e4 → d5

is represented as:

exd5

Castling uses:

O-O
O-O-O

Promotion adds:

=Q

or the selected promotion piece.

Move history is displayed in two columns:

White
Black

The notation system is basic chess notation, not a complete standards-compliant SAN/PGN implementation.

Chess Clocks

The game contains an optional chess-clock system.

Available presets are:

1 + 0
3 + 0
5 + 0
10 + 0
15 + 10
30 + 0

The first number is the starting time in minutes.

The second number is the increment added after every move.

Timer Accuracy

The timer does not simply subtract a fixed amount every frame.

Instead, it stores:

last_timer_update

and calculates:

elapsed = now - last_timer_update

This measures actual elapsed time.

This is more accurate than assuming every rendered frame takes exactly the same amount of time.

For example, if the game temporarily slows from 60 FPS to 30 FPS, the clock does not accidentally run at half speed.

Timer and Game State

The timer stops updating while:

game_over

is true.

It also pauses while:

animation

or:

promotion_pending

is active.

This prevents a player from losing time while waiting for a promotion choice or while a move animation is playing.

When a move is completed, the increment is awarded to the player who just moved before the turn changes.

For example:

White moves
    ↓
White gets +10 seconds
    ↓
Turn becomes Black

This matches standard increment-clock behavior.

Animation System

The animation system is separate from the chess rules.

When a move occurs, the program stores information such as:

animation = {
    "piece": piece,
    "start": start,
    "end": end,
    "start_time": ...,
    "duration": ...
}

The board has already been updated.

The animation simply draws another copy of the moved piece traveling from its old square to its new square.

Animation Interpolation

The piece position is calculated using interpolation between its starting and ending coordinates.

The program uses a quintic easing function:

progress ** 3 * (
    progress * (progress * 6 - 15) + 10
)

This creates smooth acceleration and deceleration.

The piece also follows a small arc using:

math.sin(math.pi * progress)

This makes it appear to lift slightly during movement.

The piece becomes slightly larger around the middle of the animation.

The result is intended to make the piece appear to be physically lifted and placed instead of simply sliding across the board.

Graphical User Interface

The board occupies the left 720×720 pixels.

The right panel is 380 pixels wide.

The visual theme uses:

Several shades of green
Dark interface panels
Separate visual colors for selected squares
Legal moves
Captures
Check
Buttons
Active clocks
Move Highlights

When a piece is selected:

selected

stores its coordinates.

Then:

valid_moves

contains the legal destinations returned by:

get_legal_moves()

The interface displays:

A highlighted border around the selected piece
Small circles for empty legal destinations
Rings for legal captures

The UI does not calculate its own moves.

It directly displays the moves calculated by the chess rules engine.

Check Highlighting

If:

is_in_check(turn)

is true, the program:

Finds the king.
Creates a translucent red overlay.
Draws it over the king's square.
Draws a red border around that square.

This visually indicates that the current player must respond to check.

Promotion Interface

Promotion is treated as a modal state.

When:

promotion_pending

is not None, normal board input is temporarily disabled.

The board is darkened and a dialog displays:

Queen
Rook
Bishop
Knight

This prevents clicks intended for the promotion interface from accidentally being interpreted as chess moves.

Input Handling

All mouse input is handled by:

handle_click(pos)

The function determines whether the click occurred in:

The promotion menu
The right-side controls
The chessboard

There are several input-priority rules.

Promotion Has Priority

If promotion is active:

if promotion_pending:

the click is sent to:

handle_promotion_click()

and no normal chess move can occur.

Animation Has Priority

If an animation is playing:

if animation:
    return

board clicks are ignored.

This prevents another move from being made before the previous animation finishes.

Game Over Has Priority

If:

game_over

is true, board moves are ignored.

The player must restart the game to continue.

Selecting a Piece

If no piece is selected:

selected is None

the program checks the clicked square.

A piece can only be selected if:

piece exists

and:

piece.color == turn

Therefore, players cannot select the opponent's pieces.

Selecting a Destination

If a piece is already selected, the program checks:

elif (row, col) in valid_moves:

If the clicked square is legal:

make_move(selected, (row, col))

is called.

If the destination is not legal, the program either:

Selects another friendly piece.
Clears the selection.

Therefore, normal board input cannot send an illegal destination to make_move().

Game Loop

The main loop continuously performs four major tasks:

Process events
Update timers
Draw the interface
Maintain the frame rate

The loop runs continuously:

while True:

Pygame events are processed first.

Mouse clicks are sent to handle_click().

The timer is then updated.

Finally, the screen is redrawn.

Rendering Order

The game draws its elements in this order:

Background
    ↓
Board
    ↓
Move Highlights
    ↓
Stationary Pieces
    ↓
Move Animation
    ↓
Promotion Menu
    ↓
Display Update

The animated piece is drawn after stationary pieces so it appears above the board during movement.

The promotion menu is drawn last so it appears above the board and visually blocks the underlying interface.

Restarting the Game

restart_game() resets the complete game state.

It recreates:

board = create_board()

and resets:

turn
selected
valid_moves
en_passant_target
game_over
game_message
move_history
animation
promotion_pending

It also resets both chess clocks.

This prevents information from the previous game from carrying into the new game.

Important Design Decisions
1. Pseudo-Legal vs. Legal Moves

The program deliberately separates:

get_pseudo_moves()

from:

get_legal_moves()

This makes movement rules easier to reason about.

Piece movement answers:

Can this piece move this way?

Legal move validation answers:

Can this piece make this move without leaving its own king in check?

2. Simulation Instead of Explicit Pin Logic

Instead of writing separate algorithms for:

Pin detection
Discovered-check detection
King-exposure detection

the program simulates candidate moves.

A pin therefore becomes:

Move candidate
      ↓
Simulate
      ↓
King becomes attacked
      ↓
Reject

This dramatically simplifies the rules engine.

3. Direct Attack Detection

Attack detection is deliberately separate from legal movement.

The definition of an attacked square is not always identical to the definition of a legal move.

Therefore:

square_attacked()

examines attack geometry directly.

4. Board State Is Authoritative

The actual:

board

variable is the source of truth.

Animations do not temporarily modify the board.

The rules always operate on the actual board position.

This prevents animation state from interfering with chess logic.

5. Special Rules Are Centralized

Special move behavior is concentrated primarily in:

make_move()
simulate_move()
get_pseudo_moves()

This makes unusual chess rules easier to find and maintain.

Implemented Chess Rules
Rule	Implemented
Pawn movement	Yes
Pawn double move	Yes
Pawn captures	Yes
Knight movement	Yes
Bishop movement	Yes
Rook movement	Yes
Queen movement	Yes
King movement	Yes
Captures	Yes
Check detection	Yes
Checkmate detection	Yes
Stalemate detection	Yes
Pins	Yes, through simulation
Discovered attacks/checks	Yes, through simulation
Kingside castling	Yes
Queenside castling	Yes
En passant	Yes
Pawn promotion	Yes
Move history	Yes
Basic chess notation	Yes
Chess clocks	Yes
Increment time controls	Yes
Move animation	Yes
Current Limitations

The program implements the major move and king-safety rules but does not currently implement every possible chess draw or notation feature.

It does not contain dedicated systems for:

Threefold repetition
The fifty-move rule
Automatic insufficient-material detection
Complete FIDE/official SAN notation
PGN import/export
Position import/export
Chess AI
Network multiplayer

The notation system is therefore best described as basic chess notation, rather than a complete standards-compliant PGN/SAN system.

For example, the program records:

Captures
Castling
Promotion

but does not append check or checkmate symbols to ordinary move notation.

Function Reference
Board and Piece Functions
Piece(color, piece_type)

Creates a chess piece.

Stores:

Color
Type
Whether it has moved
create_board()

Creates the standard starting position.

copy_board()

Creates an independent copy of the current board, including copied Piece objects.

Used for move simulation.

find_king(color)

Searches the board for the specified side's king.

opposite(color)

Returns the opposing color.

in_bounds(row, col)

Determines whether a board coordinate is inside the 8×8 board.

Chess Rules Functions
square_attacked(row, col, attacking_color)

Determines whether a square is attacked by a side.

Checks:

Pawns
Knights
Kings
Rooks
Queens
Bishops
is_in_check(color)

Determines whether the specified king is currently attacked.

get_sliding_moves(row, col, color, directions)

Generates ray-based moves for:

Bishops
Rooks
Queens
get_pseudo_moves(row, col)

Generates moves that follow piece movement rules without considering whether they expose the king.

simulate_move(start, end)

Temporarily performs a move on a copied board and checks whether the moving side's king becomes unsafe.

get_legal_moves(row, col)

Filters pseudo-legal moves through simulate_move().

This is the primary legal-move generator.

has_legal_moves(color)

Determines whether a side has at least one legal move.

check_game_state()

Determines whether the current position is:

Normal
Check
Checkmate
Stalemate
Move Functions
make_move(start, end)

Executes a legal move and handles:

Captures
En passant
Castling
Promotion preparation
Move notation
En passant target
Animation
finish_move(notation)

Completes move bookkeeping.

It:

Records the move.
Gives the increment.
Switches turns.
Updates the timer timestamp.
Checks the new game state.
choose_promotion(piece_type)

Converts a promoted pawn into the selected piece.

square_name(row, col)

Converts internal coordinates into algebraic notation.

Examples:

(7, 0) → a1
(7, 4) → e1
(0, 4) → e8
Timer Functions
reset_timer()

Resets both clocks to the currently selected time control.

update_timer()

Subtracts real elapsed time from the active player's clock.

format_time(seconds)

Converts seconds into displays such as:

10:00
3:42
1:02:15
toggle_timer()

Turns the chess clock on or off.

select_timer_preset(index)

Changes the selected time control and resets both clocks.

white_time_increment()

Adds the configured increment to White.

black_time_increment()

Adds the configured increment to Black.

UI Functions
draw_board()

Draws the chessboard and check indicators.

draw_highlights()

Draws the selected square and legal-move indicators.

draw_piece(piece, x, y, scale=1.0)

Renders a Unicode chess piece.

draw_pieces()

Draws all stationary pieces.

update_animation()

Draws the currently animated piece.

draw_clock(x, y, color, seconds)

Draws a player's chess clock.

draw_button(rect, label, active=False)

Draws a reusable UI button.

draw_history()

Draws:

Move history
Chess clocks
Time controls
Timer button
New Game button
draw_status()

Displays:

Whose turn it is
Check
Checkmate
Stalemate
Time victory
draw_promotion_menu()

Draws the promotion selection interface.

Input Functions
handle_click(pos)

Central mouse-input handler.

Determines whether the player clicked:

Promotion controls
Timer controls
New Game
A chess piece
A chess destination
handle_promotion_click(pos)

Processes clicks in the promotion selection menu.

Complete Move Flow


This is essentially the core architecture of the entire chess engine.

Example: Moving a Pinned Piece

Consider:

8  . . . . r . . .
7  . . . . . . . .
6  . . . . . . . .
5  . . . . R . . .
4  . . . . . . . .
3  . . . . . . . .
2  . . . . . . . .
1  . . . . K . . .
   a b c d e f g h

White's rook on e5 is between the white king and black rook.

Suppose White attempts:

Re5 → a5

The program does not need to know:

"This rook is pinned."

Instead:

Step 1

get_pseudo_moves() determines that a5 is a valid rook destination.

Step 2

get_legal_moves() calls:

simulate_move((4, 4), (4, 0))
Step 3

The copied board becomes approximately:

8  . . . . r . . .
...
5  R . . . . . . .
...
1  . . . . K . . .
Step 4

The program calls:

is_in_check("white")
Step 5

find_king("white") finds the king on e1.

Step 6

square_attacked() traces upward from the king.

It finds the black rook on e8 with no white rook blocking it.

Therefore:

is_in_check("white")

returns:

True
Step 7

simulate_move() returns:

True

meaning the simulated position is unsafe.

Step 8

get_legal_moves() does not add the move.

The player therefore never sees that destination as legal.

This is how the program detects pins without a dedicated pin algorithm.

Example: Checkmate Detection

Suppose Black has just moved and the turn changes to White.

finish_move() calls:

check_game_state()

The first question is:

has_legal_moves("white")

The function checks every White piece.

For each piece it calls:

get_legal_moves()

Every candidate move is simulated.

Eventually, suppose no legal move is found:

has_legal_moves("white")

returns:

False

The program then asks:

is_in_check("white")

If that returns:

True

then:

White has no legal moves
+
White is in check
=
Checkmate

The game ends and the message becomes:

Checkmate — Black wins!
Project Structure

The project is primarily organized as one Python source file.

Conceptually, it contains:

The source code is deliberately organized into sections so the graphical, timing, and chess-rule systems can be located independently.

Overall Algorithm

The entire chess engine can ultimately be reduced to one central process:

A piece has movement rules.
        ↓
Generate moves allowed by those rules.
        ↓
Pretend each move happened.
        ↓
Find the moving player's king.
        ↓
Determine whether the opponent attacks it.
        ↓
If attacked:
    reject the move.
Else:
    accept the move.

This single process is responsible for a surprisingly large amount of chess functionality.

It automatically handles:

Normal legal moves
Pins
Discovered attacks
Illegal king moves
Blocking checks
Capturing checking pieces
Moving while in check
Castling safety
En passant king-safety situations
Checkmate
Stalemate

Special rules such as castling, en passant, and promotion still require additional state and move-execution logic, but the underlying king-safety principle remains the same.

Core Architecture



The graphical interface sits on top of this engine and displays:

Board state
Legal moves
Checks
Animations
Chess clocks
Promotion choices
Move history
Conclusion

This project is more than a graphical chessboard. Its core is a small chess rules engine built around:

Move generation
Board simulation
Attack detection
King-safety validation
Game-state detection

The central relationship is:

Movement Rules
      
Pseudo-Legal Moves
      
Move Simulation
      
Attack Detection
      
King Safety
      
Legal Moves

The important design choice is that complicated tactical rules do not each require their own specialized algorithm.

Instead, many of them emerge from the same principle:

After a move, your own king must not be attacked.

This allows the engine to automatically handle pins, discovered attacks, illegal king moves, blocking checks, capturing checking pieces, castling safety, and en passant king-safety situations.

The board stores the position, pseudo-move generation determines what pieces can physically do, simulation determines what they are legally allowed to do, attack detection determines king safety, and the game-state system determines whether the game can continue.

The result is a compact rules architecture supporting a complete playable chess game while keeping the graphical interface, timing system, animation system, and chess logic largely separated.