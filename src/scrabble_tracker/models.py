"""Domain entities (SQLAlchemy 2.0 declarative models).

Entities:
    User        -- a registered account.
    Game        -- one Scrabble game (multiplayer or solo).
    GamePlayer  -- a participant (registered user or guest) in one game.
    Turn        -- one move inside a game.

Calculations that depend only on the state of an entity (running score,
ranking, user statistics) live here as properties. Use cases that
orchestrate several entities and side effects live in ``services/``
(separation of concerns, SWEBOK KA03). All timestamps are naive UTC.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


TURN_TYPES: tuple[str, ...] = ("normal", "scrabble", "foul", "pass", "exchange")
#: Turn types that never score points, by the rules of the game.
ZERO_POINT_TURN_TYPES: tuple[str, ...] = ("foul", "pass", "exchange")
GAME_MODES: tuple[str, ...] = ("multiplayer", "individual")
STATUS_IN_PROGRESS = "in_progress"
STATUS_FINISHED = "finished"
GAME_STATUSES: tuple[str, ...] = (STATUS_IN_PROGRESS, STATUS_FINISHED)


def utcnow() -> dt.datetime:
    """Current UTC time as a naive datetime (stored as such everywhere)."""
    return dt.datetime.now(dt.UTC).replace(tzinfo=None)


def _in_clause(column: str, values: tuple[str, ...]) -> str:
    """Build ``column IN ('a', 'b')`` from trusted constants."""
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


class Base(DeclarativeBase):
    """Declarative base class for all models."""


class User(Base):
    """A registered account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)

    game_players: Mapped[list[GamePlayer]] = relationship(back_populates="user")

    # -- Statistics (RF-03) -------------------------------------------
    def finished_participations(self) -> list[GamePlayer]:
        return [gp for gp in self.game_players if gp.game.status == STATUS_FINISHED]

    @property
    def total_games(self) -> int:
        return len(self.finished_participations())

    @property
    def average_score(self) -> float:
        parts = self.finished_participations()
        if not parts:
            return 0.0
        return round(sum(p.final_score for p in parts) / len(parts), 1)

    @property
    def best_score(self) -> int:
        return max((p.final_score for p in self.finished_participations()), default=0)

    @property
    def total_scrabbles(self) -> int:
        return sum(gp.scrabble_count for gp in self.game_players)

    @property
    def wins(self) -> int:
        """Games won. Ties are awarded to the earliest player in turn order."""
        wins = 0
        for gp in self.finished_participations():
            ranking = gp.game.ranking()
            if ranking and ranking[0][0].id == gp.id:
                wins += 1
        return wins

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.username!r}>"


class Game(Base):
    """One Scrabble game."""

    __tablename__ = "games"
    __table_args__ = (
        CheckConstraint(_in_clause("mode", GAME_MODES), name="ck_game_mode"),
        CheckConstraint(_in_clause("status", GAME_STATUSES), name="ck_game_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    mode: Mapped[str] = mapped_column(String(20), default="multiplayer")
    language: Mapped[str] = mapped_column(String(5), default="es")
    status: Mapped[str] = mapped_column(
        String(20), default=STATUS_IN_PROGRESS, index=True
    )
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)
    finished_at: Mapped[dt.datetime | None] = mapped_column(DateTime)

    created_by: Mapped[User | None] = relationship()
    players: Mapped[list[GamePlayer]] = relationship(
        back_populates="game",
        cascade="all, delete-orphan",
        order_by="GamePlayer.turn_order",
    )

    def average_score(self) -> float:
        """Average running score across all players (RF-10)."""
        if not self.players:
            return 0.0
        return round(sum(p.current_score for p in self.players) / len(self.players), 1)

    def ranking(self) -> list[tuple[GamePlayer, int]]:
        """Players sorted by score, highest first (RF-15).

        Uses the final score once the game is finished, the running score
        otherwise. The sort is stable, so ties keep turn order.
        """
        scored = [
            (p, p.final_score if self.status == STATUS_FINISHED else p.current_score)
            for p in self.players
        ]
        return sorted(scored, key=lambda pair: pair[1], reverse=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Game {self.id} {self.mode} {self.status}>"


class GamePlayer(Base):
    """A participant (registered user or guest) in one game."""

    __tablename__ = "game_players"

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    guest_name: Mapped[str | None] = mapped_column(String(64))
    turn_order: Mapped[int] = mapped_column(Integer, default=0)

    remaining_tiles: Mapped[str | None] = mapped_column(String(32))
    tile_penalty: Mapped[int] = mapped_column(Integer, default=0)
    tile_bonus: Mapped[int] = mapped_column(Integer, default=0)
    finished_rack_first: Mapped[bool] = mapped_column(Boolean, default=False)

    game: Mapped[Game] = relationship(back_populates="players")
    user: Mapped[User | None] = relationship(back_populates="game_players")
    turns: Mapped[list[Turn]] = relationship(
        back_populates="player",
        cascade="all, delete-orphan",
        order_by="Turn.sequence",
    )

    @property
    def display_name(self) -> str:
        if self.user is not None:
            return self.user.username
        return self.guest_name or "Player"

    @property
    def current_score(self) -> int:
        """Running score without the closing rule applied (RF-09)."""
        return sum(t.points for t in self.turns)

    @property
    def final_score(self) -> int:
        """Score including the closing penalty and bonus, if applied."""
        return self.current_score - (self.tile_penalty or 0) + (self.tile_bonus or 0)

    @property
    def scrabble_count(self) -> int:
        return sum(1 for t in self.turns if t.turn_type == "scrabble")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<GamePlayer {self.display_name!r}>"


class Turn(Base):
    """One move inside a game."""

    __tablename__ = "turns"
    __table_args__ = (
        CheckConstraint(_in_clause("turn_type", TURN_TYPES), name="ck_turn_type"),
        CheckConstraint("points >= 0", name="ck_turn_points_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    game_player_id: Mapped[int] = mapped_column(
        ForeignKey("game_players.id", ondelete="CASCADE"), index=True
    )
    sequence: Mapped[int] = mapped_column(Integer, default=0)
    turn_type: Mapped[str] = mapped_column(String(20), default="normal")
    word: Mapped[str | None] = mapped_column(String(64))
    points: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)

    player: Mapped[GamePlayer] = relationship(back_populates="turns")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Turn {self.turn_type} {self.points}>"
