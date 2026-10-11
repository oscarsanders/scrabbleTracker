"""models.py statistics (RF-03) and views.py (RF-04)."""

from scrabble_tracker import views
from scrabble_tracker.models import TURN_TYPES
from scrabble_tracker.services import games


def test_turn_types_match_ui_labels():
    from scrabble_tracker.ui.labels import TURN_TYPE_LABELS

    assert set(TURN_TYPES) == set(TURN_TYPE_LABELS)


def _finished_duel(session, alice, bob):
    game = games.start_game(
        session, creator=alice, mode="multiplayer", language="es", other_players="bob"
    )
    p1, p2 = game.players
    games.add_turn(
        session,
        game=game,
        player_id=p1.id,
        turn_type="scrabble",
        word="QUIJOTE",
        points=68,
    )
    games.add_turn(
        session, game=game, player_id=p2.id, turn_type="normal", word="SOL", points=10
    )
    games.finish_game(session, game=game, remaining_by_player={p1.id: "", p2.id: "AE"})
    return game


def test_user_statistics(session, make_user):
    alice, bob = make_user("alice"), make_user("bob")
    _finished_duel(session, alice, bob)
    assert (alice.total_games, alice.wins, alice.total_scrabbles) == (1, 1, 1)
    assert alice.best_score == alice.average_score == 70
    assert (bob.wins, bob.best_score) == (0, 8)
    empty = make_user("carol")
    assert (empty.total_games, empty.average_score, empty.best_score) == (0, 0.0, 0)


def test_history_and_profile_views(session, make_user):
    alice, bob = make_user("alice"), make_user("bob")
    game = _finished_duel(session, alice, bob)
    (row,) = views.build_history(bob)
    assert (row.game_id, row.final_score, row.position, row.players) == (
        game.id, 8, 2, 2,
    )
    assert views.build_profile(alice).wins == 1


def test_game_view_orders_ranking_and_turns_newest_first(session, make_user):
    alice, bob = make_user("alice"), make_user("bob")
    game = _finished_duel(session, alice, bob)
    view = views.build_game_view(game)
    assert view.is_finished
    assert [p.name for p in view.ranking] == ["alice", "bob"]
    assert [name for _, name in view.roster] == ["alice", "bob"]
    assert view.turns[0].player == "bob"  # recorded last
    assert view.ranking[1].penalty == 2 and view.ranking[0].bonus == 2


def test_active_game_labels(session, make_user):
    alice = make_user()
    game = games.start_game(session, creator=alice, mode="individual", language="en")
    (active,) = views.build_active_games([game])
    assert active.game_id == game.id
    assert "alice" in active.label and "EN" in active.label
