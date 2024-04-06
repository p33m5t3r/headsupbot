import numpy as np
from deuces import Card, Deck, Evaluator
from enum import Enum
from typing import Union

class ActionType(Enum):
    # player events
    Fold = "fold"
    Check = "check"
    Call = "call"
    Bet = "bet"
    Raise = "raise"
    Shove = "shove"

    # dealer events
    DealHand = "deal_hole"      # ([Card], role)
    DealStreet = "deal_street"  # ([Card], street#)
    PostBB = "post_bb"          # (amount, role)
    PostSB = "post_sb"          # (amount, role)
    HandWon = "hand_won"        # (role, amount)
    Bust = "bust"               # (role)

FOLD = ActionType.Fold
CHECK = ActionType.Check
CALL = ActionType.Call
BET = ActionType.Bet
RAISE = ActionType.Raise
SHOVE = ActionType.Shove

# a concrete action to be taken by a player
class Action:

    player_actions = [
            ActionType.Fold, ActionType.Check,
            ActionType.Call, ActionType.Bet,
            ActionType.Raise, ActionType.Shove
    ]

    def __init__(self, action_type, *args):
        self.action_type = action_type
        self.amount = args[0] if len(args) == 1 else None
        self.args = args
    
    @property
    def is_player_action(self):
        return self.action_type in Action.player_actions

    def __str__(self):
        return f"{self.action_type} {self.args}"

    def __repr__(self):
        return f"{self.action_type} {self.args}"

# an ordered list of preferences over actions
class Preference:
    def __init__(self, *args):
        self.preferences: list[Action] = args

    def __str__(self):
        return f"Preference: {self.preferences}"

    def __repr__(self):
        return f"Preference: {self.preferences}"

# a probability distribution over actions
class Strategy:
    def __init__(self, strategy: dict[Action, float]):
        self.strategy = strategy

    def __str__(self):
        return f"Strategy: {self.strategy}"

    def __repr__(self):
        return f"Strategy: {self.strategy}"

UpdateRule = Union[Preference, Strategy, Action]

# picks the best valid action according to the update rule
def match(u: UpdateRule, acts: list[Action]) -> float:
    if isinstance(u, Preference):
        for a in u.preferences:
            if a in acts:
                return a
        return None

    elif isinstance(u, Strategy):
        actions = u.strategy.keys()
        probs = u.strategy.values()
        choice = np.random.choice(actions, probs)
        if choice not in acts:
            raise ValueError("Invalid action.")
        return choice

    else:
        return u


def fold():
    return Action(ActionType.Fold)

def check():
    return Action(ActionType.Check)

def call_n(amount):
    return Action(ActionType.Call, amount)

def bet_n(amount):
    return Action(ActionType.Bet, amount)

def raise_n(amount):
    return Action(ActionType.Raise, amount)

def shove_n(amount):
    return Action(ActionType.Shove, amount)


""" RULES
pre-flop, flop: can only raise 1bb
turn, river: can only raise 2bb
3 raises per street
preflop=0, flop=1, turn=2, river=3
"""
class LimitHoldemState:
    def __init__(self, n_p0="Hero", n_p1="Villain"):
        self.history = []               # previous hands
        self.actions = []               # running hand history
        self.board   = []               # dealt board
        self.sb_amt = 0.5               # small blind value
        self.bb_amt = 1                 # big blind value
        self.pot_amount = 0             # how much is in the pot
        self.street = 0                 # current street
        self.raise_count = 0            # number of raises this hand
        self.deck = Deck()              # deck of cards
        self.evaluator = Evaluator()    # hand evaluator
        self.hand_over = False          # whether or not the hand is over
        self.game_over = False          # whether or not the game is over

        self.bb_flag     = [1   , 0   ] # which player is big blind
        self.action_flag = [0   , 1   ] # which player is acting
        self.acted       = [0   , 0   ] # which players have acted
        self.stacks      = [100 , 100 ] # stack sizes
        self.bets        = [0   , 0   ] # how much each player has bet
        self.names       = [n_p0, n_p1] # player names
        self.hands       = [[]  , []  ] # player hands

    def acting_player(self) -> int:
        return 0 if self.action_flag[0] else 1

    def bb_player(self) -> int:
        return 0 if self.bb_flag[0] else 1

    def put_action_on_bb(self):
        self.action_flag = self.bb_flag

    def facing_bet_raise(self, role=0):
        return self.bets[role] < self.bets[not role]

    def facing_call(self, role=0):
        return self.bets[role] == self.bets[not role]

    def can_cover_bet(self, role=0):
        return self.stacks[role] >= self.bets[not role]

    def has_bb_option(self, role=0):
        is_bb = self.bb_flag[role]
        return is_bb and self.street == 0 and self.facing_call(role)

    def can_raise(self, role=0):
        facing_bet_raise = self.facing_bet_raise(role)

        can_raise_normally = self.raise_count < 3 and facing_bet_raise
        can_use_option = self.raise_count < 3 and self.has_bb_option(role)
        can_pay = self.stacks[role] >= self.raise_amount()

        return (can_raise_normally or can_use_option) and can_pay

    def can_bet(self, role=0):
        havent_bet = self.bets[role] == 0
        facing_bet_raise = self.facing_bet_raise(role)

        return havent_bet and not facing_bet_raise

    def can_check(self, role=0):
        facing_bet_raise = self.facing_bet_raise(role)
        havent_bet = self.bets[role] == 0
        has_bb_option = self.has_bb_option(role)

        return not facing_bet_raise and (havent_bet or has_bb_option)

    def can_call(self, role=0):
        facing_bet_raise = self.facing_bet_raise(role)
        can_cover = self.can_cover_bet(role)
        return facing_bet_raise and can_cover
    
    def can_shove(self, role=0):
        facing_bet_raise = self.facing_bet_raise(role)
        can_call = self.can_call(role)
        return facing_bet_raise and not can_call

    def can_fold(self, role=0):
        return self.facing_bet_raise(role)

    def raise_amount(self):
        return self.bb_amt if self.street < 2 else 2 * self.bb_amt

    def bet_amount(self):
        return self.sb_amt if self.street < 2 else self.bb_amt

    def last_action(self):
        return self.actions[-1]

    def available_actions(self, role=0) -> [Action]:
        is_turn_to_act = self.action_flag[role]
        if not is_turn_to_act:
            print("Not your turn.")
            return [None]
        
        actions = []
        if self.can_check(role):
            actions.append(check())

        if self.can_bet(role):
            actions.append(bet_n(self.bet_amount()))

        if self.can_call(role):
            actions.append(call_n(self.bets[1 - role]))

        if self.can_raise(role):
            actions.append(raise_n(self.raise_amount()))

        if self.can_shove(role):
            actions.append(shove_n(self.stacks[role]))

        return actions
       

    def new_hand(self):
        # flip who is big blind, who acts first
        self.bb_flag.reverse()
        self.action_flag = self.bb_flag
        self.action_flag.reverse()

        # reset the hand history
        if self.actions:
            self.history.append(self.actions)
        self.actions = []

        # clear: board, bets, pot, hole cards, action flags,
        #        hand_over, street, raise count
        self.board = []
        self.pot_amount = 0
        self.bets = [0, 0]
        self.hands = [[], []]
        self.acted = [0, 0]
        self.street = 0
        self.raise_count = 0
        self.hand_over = False
    
        # post the blinds
        bb = self.bb_player()
        sb = not bb
        if self.stacks[bb] < self.bb_amt:
            self.game_over = True
            return False
        if self.stacks[sb] < self.sb_amt:
            self.game_over = True
            return False

        self.stacks[bb] -= self.bb_amt
        self.stacks[sb] -= self.sb_amt
        self.bets[bb] = self.bb_amt
        self.bets[sb] = self.sb_amt

        # deal hole cards
        bb_hand = self.deck.draw(2)
        sb_hand = self.deck.draw(2)
        self.hands[bb] = bb_hand
        self.hands[sb] = sb_hand

        # TODO: push onto action history
 
    def declare_winner(self, winner):
        self.stacks[winner] += self.pot_amount  # winner takes the pot
        self.hand_over = True                   # hand is over
        # push onto action history
        # TODO
 
        # further bookkeeping is done when a new hand is dealt; not here
        return True

    def showdown(self):
        p0_score = self.evaluator.evaluate(self.board, self.hands[0])
        p1_score = self.evaluator.evaluate(self.board, self.hands[1])

        winner = 0 if p0_score > p1_score else 1
        return self.declare_winner(winner)
      
    def deal_or_showdown(self):
        if self.street == 5:
            return self.showdown()
        return self.new_street()

    def new_street(self):
        # deal n cards
        if len(self.board) == 0:
            self.board = self.deck.draw(3)
        else:
            self.board.append(self.deck.draw(1))
        
        self.pot_amount += sum(self.bets)   # collect bets
        self.street += 1                    # increment street
        self.action_flag = self.bb_flag     # action to bb
        self.acted = [0, 0]                 # no one has acted
        self.bets = [0, 0]                  # no one has bet
        self.raise_count = 0                # no raises yet

        return True

    def pot_is_good(self):
        bets_eq = self.bets[0] == self.bets[1]
        both_played = self.acted[0] and self.acted[1]
        bb_no_option = not self.has_bb_option(self.bb_player())

        return bets_eq and both_played and bb_no_option

    def update(self, action: Action):
        role = self.acting_player()
        t_action = action.action_type

        self.acted[role] = 1
        
        if t_action == FOLD:
            return self.declare_winner(not role)
    
        elif t_action == CHECK:
            pass

        elif t_action == CALL:
            chips_bet = action.amount
            self.stacks[role] -= chips_bet
            self.bets[role] = self.bets[not role]

        elif t_action == BET:
            chips_bet = action.amount
            self.stacks[role] -= chips_bet
            self.bets[role] = chips_bet

        elif t_action == RAISE:
            self.raise_count += 1
            chips_bet = action.amount
            self.stacks[role] -= chips_bet
            self.bets[role] += chips_bet

        elif t_action == SHOVE:
            # TODO: implement
            chips_bet = action.amount
            self.stacks[role] -= chips_bet
            self.bets[role] = chips_bet

    def __str__(self):
        fmt = lambda cs: ','.join([Card.int_to_pretty_str(c) for c in cs])
        s_handcount = f"Hands Played: {len(self.history)}"
        s_p0s = f"p0: {self.names[0]}: {self.stacks[0]}bb"
        s_p1s = f"p1: {self.names[1]}: {self.stacks[1]}bb"
        s_p0h = fmt(self.hands[0])
        s_p1h = fmt(self.hands[1])
        s_board = fmt(self.board)
        s_pot = f"Pot: {self.pot_amount}bb"
        s_p0b = f"p0 bet: {self.bets[0]}bb"
        s_p1b = f"p1 bet: {self.bets[1]}bb"
    
        info = [s_handcount, s_p0s, s_p1s, s_p0h, 
                s_p1h, s_board, s_pot, s_p0b, s_p1b]
        return '\n'.join(info)

class LimitHoldemGame:
    def __init__(self, p0_strategy, p1_strategy):
        self.state = LimitHoldemState()
        self.strategies = [p0_strategy, p1_strategy]

    def play_hand(self):
        state = self.state
        state.new_hand()
        while not state.hand_over:
            if state.pot_is_good():
                state.deal_or_showdown()
                continue

            player = self.state.acting_player()
            strategy = self.strategies[player]
            available_actions = self.state.available_actions(player)
            action = match(
                strategy(self.state, role=player),
                available_actions
            )
            self.state.update(action)

    def play_n_hands(self, n_hands: int):
        state = self.state
        while (state.game_over == False and len(state.history) < n_hands):
            self.play_hand()


def all_cards_with_value_of(card_str):
    deck = Deck()
    card_rank = Card.new(card_str).get_rank_int()
    return [c for c in deck.cards if Card.get_rank_int(c) == card_rank]

def s_only_play_aces(state, role=1):
    hand = state.hands[role]
    aces = all_cards_with_value_of('As')
    if hand[0] not in aces or hand[1] not in aces:
        return Preference(check(), fold())
    else:
        bet_size = state.bet_amount()
        raise_size = state.raise_amount()
        return Preference(bet_n(bet_size), raise_n(raise_size))

def s_random(state, role):
    actions = state.available_actions(role)
    return Strategy({a: 1 / len(actions) for a in actions})

def oai_action(state, model, prompt):
    return [None]

LLM_PRO_PROMPT = ""
def s_gpt35_pro(state, role=1):
    return oai_action(state, "gpt-3.5", LLM_PRO_PROMPT)

def s_gpt4_pro(state, role=1):
    return oai_action(state, "gpt4", LLM_PRO_PROMPT)

def evaluate_strategy(s1, s2, gametype, n_hands):
    game_state = gametype()
    for _ in range(n_hands):
        pass

def analyze(strategies, gametype, n_hands=1000):
    outcomes = np.zeros((len(strategies), len(strategies)))
    for i, s1 in enumerate(strategies):
        for j, s2 in enumerate(strategies):
            outcomes[i, j] = evaluate_strategy(s1, s2, gametype, n_hands)
    
    # insert matplotlib boilerplate here

def cli_player(state, role):
    print(state)
    actions = state.available_actions(role)
    mapping = {i: a for i, a in enumerate(actions)}
    print(f"Available Actions: {state.available_actions(role)}")
    choice = int(input("Choose an action: "))
    return mapping[choice]
    

def play_against_cli(bot, gametype=LimitHoldemGame, n_hands=100):
    game = gametype(cli_player, bot)
    game.play_n_hands(n_hands)

if __name__ == "__main__":
    bots = []
    # analyze(bots)
    play_against_cli(s_only_play_aces)
