from gumsup4.base.models import Hand, PlayerState, Player, Trick, Group, GroupPlayer
from gumsup4.base.river_utils import build_deck, deal_cards, play_card, get_next_player_in_trick
import random


# make a group
group = Group.objects.create()
print(group.id)

my_player_names = ["chris1","robin1","grant","jonathan"]
for p in my_player_names:
	player, created = Player.objects.get_or_create(name=p)
	gp = GroupPlayer.objects.create(group=group,player=player)

# Create a test hand
deck = build_deck()
random.shuffle(deck)
hand = Hand.objects.create(deck=deck,current_turn=group.players.all()[0])
print(f"current turn: {hand.current_turn}")

# Create player states
player_states = []
for p in group.players.all():
	p_state = PlayerState.objects.create(hand=hand, player=p)
	player_states.append(p_state)

# Deal cards
deal_cards(hand, num_cards=5)
for p in player_states:
	print(p.player.name)
	p.refresh_from_db()

	# Play a card
	card_to_play = p.cards[0]
	complete = play_card(hand, p, card_to_play)


