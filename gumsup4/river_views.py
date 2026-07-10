from django.shortcuts import render, redirect, get_object_or_404
from .base.models import Group, Player, RiverGame, Hand, PlayerState
from .base.river_utils import new_hand

def group_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    player_id = request.session.get("player_id")

    if player_id:
        # Already joined
        player = Player.objects.get(id=player_id, group=group)
        players = group.players.all()
        return render(request, "river/group.html", {"group": group, "player": player, "players": players})

    if request.method == "POST":
        name = request.POST["name"]
        player = Player.objects.create(group=group, name=name)
        request.session["player_id"] = str(player.id)
        return redirect("river_group", group_id=group_id)

    return render(request, "river/join_group.html", {"group": group})


def new_game_view(request):

    player_id = request.session.get("player_id")
    player = Player.objects.get(id=player_id)
    group = player.group

    if request.method == "POST":
        game = RiverGame.objects.create(group=group)
        hand = new_hand(game)
        return redirect("river_game", game_id=game.id)


    if player_id:
        # Already joined
        player = Player.objects.get(id=player_id, group=group)
        players = group.players.all()
        return render(request, "river/group.html", {"group": group, "player": player, "players": players})

    return render(request, "river/join_group.html", {"group": group})

def game_view(request,game_id):
    game = get_object_or_404(RiverGame, id=game_id)
    hand = game.hands.last()
    player = get_object_or_404(Player, id=request.session.get("player_id"))
    player_state = get_object_or_404(PlayerState, hand=hand,player=player)

    return render(request, "river/game.html", {"game": game,"hand": hand, "player": player, "player_state": player_state})