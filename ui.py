import curses
from enum import Enum

class Color(Enum):
    WHITE_ON_BLUE = 1
    YELLOW_ON_BLACK = 2
    RED_ON_WHITE = 3
    BLACK_ON_WHITE = 4
    WHITE_ON_BLACK = 5

class Box:
    def __init__(self, stdscr, y, x, height, width, 
                color=Color.WHITE_ON_BLUE):
        self.stdscr = stdscr
        self.y = y
        self.x = x
        self.height = height
        self.width = width
        self.color = color

def draw_box_border(box: Box, color=None):
    stdscr, y, x = box.stdscr, box.y, box.x
    height, width = box.height, box.width
    color = box.color if color is None else color

    stdscr.attron(curses.color_pair(color.value))
    stdscr.addstr(y, x, "┌" + "─" * (width - 2) + "┐")
    for i in range(y + 1, y + height - 1):
        stdscr.addstr(i, x, "│" + " " * (width - 2) + "│")
    stdscr.addstr(y + height - 1, x, "└" + "─" * (width - 2) + "┘")
    stdscr.attroff(curses.color_pair(color.value))

def highlight_box_border(box: Box):
    stdscr, y, x = box.stdscr, box.y, box.x
    height, width, color = box.height, box.width, box.color

    stdscr.attron(curses.color_pair(color.value))
    stdscr.addstr(y, x, "┏" + "━" * (width - 2) + "┓")
    for i in range(y + 1, y + height - 1):
        stdscr.addstr(i, x, "┃" + " " * (width - 2) + "┃")
    stdscr.addstr(y + height - 1, x, "┗" + "━" * (width - 2) + "┛")
    stdscr.attroff(curses.color_pair(color.value))

def draw_text_in_box(box: Box, text: str, color=None, xoff=0, yoff=0):
    color = box.color if color is None else color
    stdscr, y, x = box.stdscr, box.y, box.x

    stdscr.attron(curses.color_pair(color.value))
    lines = text.split("\n")
    for i, line in enumerate(lines):
        stdscr.addstr(y + i + 1 + yoff, x + 2 + xoff, line)
    stdscr.attroff(curses.color_pair(color.value))

def coords(stdscr, x_percent, y_percent):
    screen_height, screen_width = stdscr.getmaxyx()
    y = int(screen_height * y_percent)
    x = int(screen_width * x_percent)
    return x, y

def box_centered_at(stdscr, x_percent, y_percent, width, height):
    x, y = coords(stdscr, x_percent, y_percent)
    return Box(stdscr, y - height // 2, x - width // 2, height, width)

def box_following_h(stdscr, box, gap=0, h=None, w=None):
    height = box.height if h is None else h
    width = box.width if w is None else w
    x, y = box.x + box.width + gap, box.y
    return Box(stdscr, y, x, height, width, color=box.color)

def box_following_v(stdscr, box, gap=0, w=None, h=None):
    height = box.height if h is None else h
    width = box.width if w is None else w
    x, y = box.x, box.y + box.height + gap
    return Box(stdscr, y, x, height, width, color=box.color)

def color_of_card(card: str):
    return Color.RED_ON_WHITE if card[1] in ['h', 'd'] else Color.BLACK_ON_WHITE

def draw_board_on_box(box: Box, board: list[str]):
    stdscr = box.stdscr
    board_str_len = len(" ".join(board))
    box_center = box.x + box.width // 2
    start_x = box_center - board_str_len // 2
    current_x = start_x

    for card in board:
        color = curses.color_pair(color_of_card(card).value)
        stdscr.attron(color)
        stdscr.addstr(box.y + 1, current_x, card)
        current_x += len(card) + 1
        stdscr.attroff(color)

def draw_text_at_box_center(box: Box, text: str, color=None, y_offset=-1):
    if color is None:
        color = box.color

    stdscr = box.stdscr
    y = box.y + y_offset
    x = box.x + (box.width - len(text)) // 2

    stdscr.attron(curses.color_pair(color.value))
    stdscr.addstr(y, x, text)
    stdscr.attroff(curses.color_pair(color.value))

def draw_text_at_box_start(box: Box, text: str, color=None, x_offset=0, y_offset=1):
    if color is None:
        color = box.color

    stdscr = box.stdscr
    y = box.y + y_offset
    x = box.x + x_offset

    stdscr.attron(curses.color_pair(color.value))
    stdscr.addstr(y, x, text)
    stdscr.attroff(curses.color_pair(color.value))

def draw_box_solid(box: Box, color=None):
    if color is None:
        color = box.color

    stdscr = box.stdscr
    y, x = box.y, box.x
    height, width = box.height, box.width

    stdscr.attron(curses.color_pair(color.value))
    for i in range(y, y + height):
        stdscr.addstr(i, x, " " * width)
    stdscr.attroff(curses.color_pair(color.value))

def draw_pot_text(board_box: Box, pot_value: float):
    draw_text_at_box_center(
        board_box, f"pot: {pot_value}bb", 
        color=Color.YELLOW_ON_BLACK,
        y_offset=0
    )

# assumes we're drawing on a box with standard player box geometry
def draw_hand_in_box(box, hand: list[str], visible=True):
    if len(hand) != 2:
        raise ValueError("Hand should have 2 cards")
    cards = ["??", "??"] if not visible else hand
    c0_color = color_of_card(cards[0])
    c1_color = color_of_card(cards[1])
    x_start = box.x + 9     # hardcoded for now
    draw_text_in_box(box, cards[0], color=c0_color, xoff=x_start, yoff=1)
    draw_text_in_box(box, cards[1], color=c1_color, xoff=x_start + 3, yoff=1)
    

def main(stdscr):
    # Initialize colors
    curses.init_pair(Color.WHITE_ON_BLUE.value, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(Color.YELLOW_ON_BLACK.value, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(Color.RED_ON_WHITE.value, curses.COLOR_RED, curses.COLOR_WHITE)
    curses.init_pair(Color.BLACK_ON_WHITE.value, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(Color.WHITE_ON_BLACK.value, curses.COLOR_WHITE, curses.COLOR_BLACK)

    # Clear screen
    stdscr.clear()

    # Set up state variables
    board = ['Ah', '7s', '3d', 'Qh', 'Kc']
    pot_amount = 81
    action_on_hero = True
    blind_on_hero = False
    prior_action = "raise"
    hero_bet = 10
    villian_bet = 20
    hero_stack = 90
    villian_stack = 80
    hero_name = "Hero"
    villian_name = "Poker Bot"
    can_see_villian_hand = False
    hero_hand = ["As", "Ks"]
    villian_hand = ["Qs", "Qd"]
    # subset of ["fold", "check", "call", "bet N", "raise N", "all-in"]
    available_actions = ["fold", "call", "raise"]
    available_bets = ["1/4", "1/3", "1/2", "2/3", "3/4", "pot"]

    # Set up some reference geometry and box sizing information 
    screen_height, screen_width = stdscr.getmaxyx()
    pb_text_max_chars = 25
    pb_border_width = 2
    pb_height = 4
    pb_width = pb_text_max_chars + 2 * pb_border_width
    pb_gap = 2
    board_gap = 2
    max_action_width = 6
    max_bet_width = 4       # 9999 max bet; assuming integer bets
    # Create boxes
    villian_box = box_centered_at(stdscr, 0.5, 0.2, pb_width, pb_height)
    villian_action_box = box_following_v(
        stdscr, villian_box, gap=0, h=1, w=max_action_width
    )
    villian_bet_box = box_following_h(
        stdscr, villian_action_box, gap=1, h=1, w=max_bet_width
    )
    board_box = box_following_v(stdscr, villian_box, gap=board_gap, h=3)
    hero_action_box = box_following_v(stdscr, board_box, gap=pb_gap-1, h=1, w=max_action_width)
    hero_bet_box = box_following_h(stdscr, hero_action_box, gap=1, h=1, w=max_bet_width)
    hero_box = box_following_v(stdscr, hero_action_box, gap=0, h=pb_height, w=pb_width)

    # Draw boxes
    draw_box_border(hero_box)
    draw_box_border(villian_box)
    draw_box_solid(villian_action_box, color=Color.YELLOW_ON_BLACK)
    draw_box_solid(hero_action_box, color=Color.YELLOW_ON_BLACK)
    draw_box_border(board_box, color=Color.YELLOW_ON_BLACK)
    draw_board_on_box(board_box, board)
    draw_pot_text(board_box, pot_amount)
    # draw_box_solid(hero_bet_box)
    # draw_box_solid(villian_bet_box)

    if action_on_hero:
        highlight_box_border(hero_box)
        draw_text_at_box_start(villian_action_box, prior_action, y_offset=0, color=Color.WHITE_ON_BLACK)
    else:
        highlight_box_border(villian_box)
        draw_text_at_box_start(hero_action_box, prior_action, y_offset=0, color=Color.WHITE_ON_BLACK)

    if blind_on_hero:
        draw_text_at_box_center(hero_box, " ⓑ ", y_offset=0)
    else:
        draw_text_at_box_center(villian_box, " ⓑ ", y_offset=villian_box.height-1)

    # Populate the hero/villian boxes
    draw_text_at_box_start(hero_bet_box, str(hero_bet), color=Color.WHITE_ON_BLACK, y_offset=0)
    draw_text_at_box_start(villian_bet_box, str(villian_bet), color=Color.WHITE_ON_BLACK, y_offset=0)
    draw_text_in_box(villian_box, villian_name, color=Color.YELLOW_ON_BLACK)
    draw_text_in_box(hero_box, hero_name, color=Color.YELLOW_ON_BLACK)
    draw_text_in_box(villian_box, str(villian_stack) + "bb", color=Color.WHITE_ON_BLUE, yoff=1)
    draw_text_in_box(hero_box, str(hero_stack) + "bb", color=Color.WHITE_ON_BLUE, yoff=1)
    draw_hand_in_box(hero_box, hero_hand, visible=True)
    draw_hand_in_box(villian_box, villian_hand, visible=can_see_villian_hand)

    # now we just need to draw the action buttons

    # Refresh the screen
    stdscr.refresh()

    # Event main loop
    while True:
        key = stdscr.getch()
        if key == ord('q'):
            break
        # Add your event handling code here

if __name__ == "__main__":
    curses.wrapper(main)
