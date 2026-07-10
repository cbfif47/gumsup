from .models import Hand, PlayerState, Trick, RiverGame
import random


SUITS = ["hearts", "diamonds", "clubs", "spades"]
RANKS = [
    ("2", 2), ("3", 3), ("4", 4), ("5", 5),
    ("6", 6), ("7", 7), ("8", 8), ("9", 9),
    ("10", 10), ("J", 11), ("Q", 12), ("K", 13), ("A", 14),
]

def build_deck():
    """Return a list of 52 card dicts"""
    return [
        {"suit": suit, "rank": rank, "value": value}
        for suit in SUITS
        for rank, value in RANKS
    ]


def deal_cards(hand):
    """
    Deal `num_cards` cards to each player in the hand.
    Removes those cards from the deck as they're dealt.
    """
    deck = hand.deck[:]  # copy current deck
    updated_players = []
    num_cards = hand.num_of_tricks

    for state in hand.player_states.all():
        # Take num_cards from the top of the deck
        new_cards = deck[:num_cards]
        deck = deck[num_cards:]

        # Add to player's existing cards (support multi-round dealing)
        state.cards = new_cards
        state.save()
        updated_players.append(state)

    hand.trump_suit = deck[0].get("suit")
    deck = deck[0:]
    # Save the updated deck back to the hand
    hand.deck = deck
    hand.save()

    return updated_players


def new_hand(game):
    deck = build_deck()
    random.shuffle(deck)
    hands_so_far = game.hands.count()
    # now deal
    if hands_so_far < 7:
        num_of_tricks = hands_so_far + 1
    else:
        num_of_tricks = 14 - hands_so_far # down the river
    turn = hands_so_far % game.group.players.count()
    hand = Hand.objects.create(game=game,deck=deck,current_turn=game.group.players.all()[turn], num_of_tricks=num_of_tricks)

    player_states = []
    for p in game.group.players.all():
        # delete old player states
        PlayerState.objects.filter(player=p).delete()
        # make new ones
        p_state = PlayerState.objects.create(hand=hand, player=p)
        player_states.append(p_state)

    # now deal
    if hands_so_far < 7:
        num_cards = hands_so_far + 1
    else:
        num_cards = 14 - hands_so_far # down the river
    deal_cards(hand)

    return hand


def get_next_player_in_trick(hand, current_player):
    """
    Returns the next player who hasn't played in the current trick.
    Returns None if all players have played (trick complete).
    """
    players_in_order = list(hand.players.all())
    current_index = players_in_order.index(current_player)

    current_trick = hand.tricks.last()
    played_player_ids = {play["player_id"] for play in current_trick.played_cards}

    for offset in range(1, len(players_in_order)+1):
        candidate = players_in_order[(current_index + offset) % len(players_in_order)]
        if str(candidate.id) not in played_player_ids:
            return candidate

    # Everyone has played
    return None


def determine_winner(trick):

    scoring_plays = [p for p in trick.played_cards if p["card"]["suit"] == trick.hand.trump_suit]
    if scoring_plays == []:
        scoring_plays = [p for p in trick.played_cards if p["card"]["suit"] == trick.lead_suit]

    winning_value = -1
    winner = None
    for p in scoring_plays:
        if p["card"]["value"] > winning_value:
            winner = p
            winning_value = p["card"]["value"]
            print("winner")
    trick.winner = Player.objects.get(id=p["player_id"])
    trick.save()

    return(trick)


def play_card(hand: Hand, player_state: PlayerState, card: dict):
    """
    Player plays a card in the current trick.
    Automatically updates PlayerState, Trick, and Hand.current_turn.
    Returns (trick, trick_complete)
    """
    complete = "NONE"
    # Check turn
    if hand.current_turn != player_state.player:
        raise ValueError("It's not this player's turn")

    # Get or create the current trick
    current_trick = hand.tricks.filter(winner=None).last()
    if current_trick is None:
        print("making new trick")
        trick_number = hand.tricks.count() + 1
        current_trick = Trick.objects.create(hand = hand,number = trick_number, lead_suit = card["suit"])

    # Add the card to the trick (also removes from player's hand and saves)
    current_trick.add_play(player_state, card)

    # Determine next player in the trick
    next_player = get_next_player_in_trick(hand, player_state.player)
    hand.current_turn = next_player
    hand.save()

    # Trick is complete if no next player
    if next_player is None:
        current_trick = determine_winner(current_trick)
        hand.current_turn = current_trick.winner
        if hand.num_of_tricks > hand.tricks.count():
            complete = "TRICK"
        else:
            complete = "HAND"
    return complete
