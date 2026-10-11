"""services/games.py: RF-06 .. RF-15, authorization (RNF-08)."""

import pytest

from scrabble_tracker.errors import DomainError, NotFoundError
from scrabble_tracker.services import games


def _solo(session, user):
    return games.start_game(session, creator=user, mode="individual", language="es")


def _duo(session, creator, other="bob"):
    return games.start_game(
        session, creator=creator, mode="multiplayer", language="es", other_players=other
    )


def _turn(session, game, index, points, turn_type="normal", word="CASA"):
    return games.add_turn(
        session,
        game=game,
        player_id=game.players[index].id,
        turn_type=turn_type,
        word=word,
        points=points,
    )


def test_solo_game_has_only_creator(session, make_user):
    game = _solo(session, make_user())
    assert game.mode == "individual" and len(game.players) == 1
    assert game.players[0].user is not None


def test_multiplayer_links_registered_users_and_guests(session, make_user):
    alice, bob = make_user("alice"), make_user("bob")
    game = _duo(session, alice, "BOB, Guest Gina")
    assert [p.display_name for p in game.players] == ["alice", "bob", "Guest Gina"]
    assert game.players[1].user_id == bob.id
    assert game.players[2].user_id is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"mode": "cooperative", "language": "es", "other_players": "bob"},
        {"mode": "multiplayer", "language": "fr", "other_players": "bob"},
        {"mode": "multiplayer", "language": "es", "other_players": ""},
        {"mode": "multiplayer", "language": "es", "other_players": "bob, BOB"},
        {"mode": "multiplayer", "language": "es", "other_players": "a, b, c, d"},
        {"mode": "multiplayer", "language": "es", "other_players": "x" * 65},
    ],
)
def test_start_game_validation(session, make_user, kwargs):
    with pytest.raises(DomainError):
        games.start_game(session, creator=make_user(), **kwargs)


def test_turns_and_running_scores(session, make_user):
    game = _duo(session, make_user())
    _turn(session, game, 0, 20)
    _turn(session, game, 0, 8, word="SOL")
    _turn(session, game, 1, 10)
    assert [p.current_score for p in game.players] == [28, 10]
    assert game.average_score() == 19.0
    assert game.ranking()[0][0] is game.players[0]


def test_special_turns_force_zero_points(session, make_user):
    game = _solo(session, make_user())
    foul = _turn(session, game, 0, 15, "foul", "XYZ")
    passed = _turn(session, game, 0, 9, "pass", "ignored")
    assert foul.points == 0 and foul.word == "XYZ"
    assert passed.points == 0 and passed.word is None


@pytest.mark.parametrize(
    ("turn_type", "points", "word"),
    [("bonus", 5, "X"), ("normal", -1, "X"), ("normal", 5, "W" * 65)],
)
def test_add_turn_validation(session, make_user, turn_type, points, word):
    game = _solo(session, make_user())
    with pytest.raises(DomainError):
        _turn(session, game, 0, points, turn_type, word)


def test_unknown_player_rejected(session, make_user):
    game = _solo(session, make_user())
    with pytest.raises(NotFoundError):
        games.add_turn(
            session, game=game, player_id=999, turn_type="normal", word="A", points=1
        )


def test_undo_last_turn(session, make_user):
    game = _solo(session, make_user())
    player = game.players[0]
    _turn(session, game, 0, 20)
    assert games.undo_last_turn(session, game=game, player_id=player.id) is True
    assert player.current_score == 0
    assert games.undo_last_turn(session, game=game, player_id=player.id) is False


def test_finish_applies_penalty_and_bonus(session, make_user):
    game = _duo(session, make_user())
    p1, p2 = game.players
    _turn(session, game, 0, 20)
    _turn(session, game, 1, 15, word="MESA")
    games.finish_game(session, game=game, remaining_by_player={p1.id: "", p2.id: "AE"})
    assert game.status == "finished" and game.finished_at is not None
    assert (p1.tile_bonus, p1.final_score) == (2, 22)
    assert (p2.tile_penalty, p2.final_score) == (2, 13)
    assert game.ranking()[0][0] is p1


def test_finish_without_finisher_only_subtracts(session, make_user):
    game = _duo(session, make_user())
    p1, p2 = game.players
    _turn(session, game, 0, 20)
    _turn(session, game, 1, 15, word="MESA")
    games.finish_game(
        session, game=game, remaining_by_player={p1.id: "AE", p2.id: "Z"}
    )
    assert (p1.final_score, p2.final_score) == (18, 5)


def test_finished_game_is_immutable(session, make_user):
    game = _solo(session, make_user())
    games.finish_game(session, game=game, remaining_by_player={})
    with pytest.raises(DomainError):
        games.finish_game(session, game=game, remaining_by_player={})
    with pytest.raises(DomainError):
        _turn(session, game, 0, 5)
    with pytest.raises(DomainError):
        games.undo_last_turn(session, game=game, player_id=game.players[0].id)


def test_rack_too_long_rejected(session, make_user):
    game = _solo(session, make_user())
    with pytest.raises(DomainError):
        games.finish_game(
            session, game=game, remaining_by_player={game.players[0].id: "A" * 33}
        )


def test_access_control_does_not_leak_existence(session, make_user):
    alice, mallory = make_user("alice"), make_user("mallory")
    game = _solo(session, alice)
    assert games.get_game_for_user(session, game.id, alice) is game
    with pytest.raises(NotFoundError) as hidden:
        games.get_game_for_user(session, game.id, mallory)
    with pytest.raises(NotFoundError) as missing:
        games.get_game_for_user(session, 12345, mallory)
    with pytest.raises(NotFoundError):
        games.get_game_for_user(session, None, mallory)
    assert str(hidden.value) == str(missing.value)


def test_list_active_and_finished(session, make_user):
    alice = make_user()
    open_game, done = _solo(session, alice), _solo(session, alice)
    games.finish_game(session, game=done, remaining_by_player={})
    assert games.list_active_games(session, alice) == [open_game]
    assert games.list_finished_games(session, alice) == [done]
