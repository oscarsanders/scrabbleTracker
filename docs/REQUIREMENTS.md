# Requirements Specification — Scrabble Tracker (stateless edition)

Process reference: ISO/IEC/IEEE 29148 and SWEBOK v4 KA01, scaled to a very
small project. No regulated data; nothing is stored (ADR-0005).

Conventions: **RF-xx** functional · **RNF-xx** non-functional (ISO/IEC 25010
attributes) · **R-xx** constraint. All verification entries are automated tests
in `tests/` unless marked *Manual*.

## Functional requirements

| ID | Requirement | Acceptance criterion | Verification |
|---|---|---|---|
| RF-01 | Start a game with 1–4 player names (comma-separated); one name is a solo game. | Empty, duplicate (case-insensitive), over-long or more than four names are rejected. | `test_game::test_new_game_*` |
| RF-02 | Choose the tile language (Spanish or English). | Unsupported languages are rejected. | `test_game::test_new_game_validation`, `test_tiles` |
| RF-03 | Record a move with word and points for a player. | The move is stored with the cleaned word. | `test_game::test_turns_and_running_scores`, `::test_special_turns_force_zero_and_clean_words` |
| RF-04 | Move types: word, scrabble (all 7 tiles), foul, pass, exchange. Foul/pass/exchange always score 0; pass/exchange carry no word. | Invalid types and invalid points (negative, fractional, boolean) are rejected. | `test_game::test_add_turn_validation`, `::test_scrabble_counter` |
| RF-05 | Show each player's running score, ordered best first (ties keep turn order). | Score equals the sum of their moves. | `test_game::test_turns_and_running_scores`, `::test_ties_keep_turn_order`, `test_presenter` |
| RF-06 | Show the game average (mean of the players' scores) and each player's average points per move, plus their scrabble and move counts. | Per-move average counts zero-point moves; counts use correct plurals ("0 scrabbles · 0 moves"). | `test_game::test_turns_and_running_scores`, `::test_average_per_move_counts_zero_point_moves`, `test_render::test_scoreboard_uses_scrabble_wording_and_per_player_average`, `::test_new_game_scoreboard_shows_zeroes` |
| RF-07 | At the end, enter each player's remaining tiles. | Racks over 32 characters are rejected and the game stays open. | `test_game::test_rack_too_long_rejected_and_game_stays_open` |
| RF-08 | Each player loses the value of their remaining tiles. | Penalty equals the tile values of the chosen language. | `test_rules`, `test_tiles`, `test_game::test_finish_without_finisher_only_subtracts` |
| RF-09 | If exactly one player empties their rack they gain the sum of the others' remaining tiles. | Bonus is applied only with exactly one finisher. | `test_rules::*`, `test_game::test_finish_applies_penalty_and_bonus` |
| RF-10 | Show the final ranking at the top, numbered 1–N, with a **Winner** badge on the top scorer (ties share the badge and position; none for solo games); a finished game cannot be modified and its move form is hidden. | Ranking uses final scores with competition ranking (1, 1, 3); further changes are rejected. | `test_game::test_finish_can_reorder_ranking`, `::test_finished_game_is_immutable`, `test_presenter::test_finished_game_shows_ranking_and_hides_racks`, `test_game::test_standings_use_competition_ranking_for_ties`, `::test_winners_*`, `test_render::test_ranking_*`, `::test_solo_ranking_has_no_winner_badge` |
| RF-11 | Undo a player's latest move while the game is in progress. | Only that player's last move is removed; nothing to undo reports so. | `test_game::test_undo_removes_only_that_players_latest_move` |
| RF-12 | Start a new game at any time, discarding the current one. | Returns to the setup screen. | *Manual* |

## Non-functional requirements

| ID | Attribute | Requirement | Verification |
|---|---|---|---|
| RNF-01 | Usability | Usable on a phone (≥ 360 px) and efficient on wide screens (up to 980 px): form and move list side by side, players in a grid, move list with bounded height. Text stays readable in light and dark mode. | *Manual* (CSS in `ui/theme.py`) |
| RNF-02 | Security / isolation | A visitor's game is held only in their own session; no module-level game state. | `test_game::test_each_game_is_independent`; design (ADR-0005) |
| RNF-03 | Privacy | Nothing is persisted: no database, no files. | Design; dependency list (only Gradio). |
| RNF-04 | Security | All user-controlled text is HTML-escaped. | `test_render::*` |
| RNF-05 | Reliability / bounds | Inputs are bounded (names, words, racks, players, moves). | `test_game::test_add_turn_validation`, `::test_turn_limit_bounds_memory` |
| RNF-06 | Portability | Runs on Python ≥ 3.11, any OS. | CI matrix 3.11–3.13 |
| RNF-07 | Deployability | Starts with no configuration; binds `$PORT` on all interfaces on Render. | `test_config::*` |
| RNF-08 | Observability | Start-up is logged to stdout as `event key=value`, safe against log injection. | `test_logging_config::*` |
| RNF-09 | Maintainability | Domain and presentation logic are pure Python, independent of Gradio. | Module structure; tests run without Gradio. |

## Constraints

| ID | Constraint |
|---|---|
| R-01 | No persistence of any kind (ADR-0005). |
| R-02 | UI framework: Gradio ≥ 6, < 7 (ADR-0002); Python ≥ 3.11. |
| R-03 | Style: PEP 8/257 via Ruff; types checked by mypy. |

## Known domain limitations

- The Spanish tile table does not model the `RR` digraph (R-05 in `RISKS.md`).
- Typing `CH`/`LL` is read as the digraph tile, never as two separate tiles.
