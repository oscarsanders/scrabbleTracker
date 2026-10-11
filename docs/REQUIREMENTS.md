# Requirements Specification — Scrabble Tracker

Process reference: ISO/IEC/IEEE 29148 (requirements engineering) and SWEBOK v4
KA01. This is a project-scoped specification *inspired by* those references; it
is not a certified conformance claim.

**Rigor level (proportionality):** small project with a *public Internet
exposure* and user accounts, so it adds a threat model, CI and operational
documentation on top of the small-project baseline (requirements, simple
architecture, version control, tests, documentation, reproducible deployment).
There is no regulated data and no safety-critical function.

## Conventions

- **RF-xx** functional requirement · **RNF-xx** non-functional requirement
  (quality attributes after ISO/IEC 25010) · **R-xx** constraint.
- *Test* = automated test (`tests/…::name`). *Manual* = verified by inspection.

## Users and context

| Role | Goal |
|---|---|
| Player | Record a game quickly from a phone, see live scores, own statistics and history. |
| Administrator | Provision and remove player accounts. |
| Maintainer | Change and deploy the code safely. |

## Functional requirements

### Accounts and sessions

| ID | Requirement | Acceptance criterion | Artifact | Verification |
|---|---|---|---|---|
| RF-01 | **Accounts are provisioned by the administrator** (changed from v1 self-registration, see ADR-0004). Usernames are 3–32 chars of `A-Za-z0-9._-`, unique case-insensitively; passwords 8–128 chars. | Invalid or duplicate usernames and short passwords are rejected; the new user can sign in. | `services/accounts.py` | `test_services_accounts::test_create_user_hashes_password`, `::test_invalid_usernames_rejected`, `::test_duplicate_username_is_case_insensitive`, `::test_admin_operations_require_admin` |
| RF-02 | Users sign in and out; the session survives page reloads for as long as the server process lives. | Valid credentials are accepted (username case-insensitive), invalid ones rejected. | `auth.py`, Gradio `launch(auth=…)` | `test_auth::test_valid_and_invalid_credentials` |
| RF-03 | The profile shows games played, average score, best score, bingos and wins. | Values equal those derived from the finished-game history. | `models.py::User`, `views.build_profile` | `test_models_views::test_user_statistics`, `::test_history_and_profile_views` |
| RF-04 | The history lists every finished game of the user with score and place. | Each finished participation appears, newest first. | `views.build_history` | `test_models_views::test_history_and_profile_views` |
| RF-05 | The administrator can add and delete accounts, except the administrator account. Deleting a user **preserves other players' game history** (participations become guests). | Deleting the admin is refused; history of shared games is unchanged. | `services/accounts.py` | `test_services_accounts::test_admin_cannot_be_deleted_and_missing_user`, `::test_delete_user_preserves_other_players_history` |
| RF-16 | A user can change their own password after re-entering the current one. | Wrong current password or weak new password is rejected. | `services/accounts.py::change_password` | `test_services_accounts::test_change_password` |

### Games

| ID | Requirement | Acceptance criterion | Artifact | Verification |
|---|---|---|---|---|
| RF-06 | *Multiplayer* (2–4 players) and *solo* modes. Names matching registered users are linked to accounts, others are guests; the creator always plays. | Mode determines the players created; limits and duplicate names are enforced. | `services/games.py::start_game` | `test_services_games::test_solo_game_has_only_creator`, `::test_multiplayer_links_registered_users_and_guests`, `::test_start_game_validation` |
| RF-07 | Each move records word and points. | The persisted move keeps both. | `models.py::Turn` | `test_services_games::test_turns_and_running_scores` |
| RF-08 | Move types: word, bingo, foul, pass, exchange. Foul/pass/exchange always score 0. | Unknown types rejected; zero-point types force 0. | `models.py::TURN_TYPES` | `test_services_games::test_special_turns_force_zero_points`, `::test_add_turn_validation`, `test_models_views::test_turn_types_match_ui_labels` |
| RF-09 | Running score per player is always visible. | Score equals the sum of the player's moves. | `GamePlayer.current_score` | `test_services_games::test_turns_and_running_scores` |
| RF-10 | The game average score is shown. | Average of all players' running scores. | `Game.average_score` | `test_services_games::test_turns_and_running_scores` |
| RF-11 | The tile language (es/en) is mandatory and selects the tile-value table. | An unsupported language is rejected. | `tiles.py`, `start_game` | `test_tiles`, `test_services_games::test_start_game_validation` |
| RF-17 | The last move of a player can be undone while the game is in progress. | Score drops accordingly; nothing to undo returns "no moves". | `services/games.py::undo_last_turn` | `test_services_games::test_undo_last_turn` |
| RF-18 | A game is visible and editable only to its participants/creator; unauthorised and non-existent games are indistinguishable. | Same error for both cases. | `services/games.py::get_game_for_user` | `test_services_games::test_access_control_does_not_leak_existence` |

### Closing a game

| ID | Requirement | Acceptance criterion | Artifact | Verification |
|---|---|---|---|---|
| RF-12 | On finishing, the remaining tiles of each player can be entered. | Racks are stored; racks over 32 chars rejected. | `services/games.py::finish_game` | `test_services_games::test_finish_applies_penalty_and_bonus`, `::test_rack_too_long_rejected` |
| RF-13 | Each player loses the value of their remaining tiles. | Penalty equals `tiles.rack_value`. | `rules.py::compute_closing` | `test_rules::*`, `test_services_games::test_finish_without_finisher_only_subtracts` |
| RF-14 | If exactly one player empties their rack, they gain the sum of the others' remaining tiles. | Bonus equals the sum of others' penalties; none otherwise. | `rules.py::compute_closing` | `test_rules::test_single_finisher_gets_bonus_and_others_pay`, `::test_two_finishers_no_bonus`, `::test_nobody_finished_only_penalties` |
| RF-15 | The final ranking is ordered by final score; a finished game cannot be modified. | Ranking is descending; further changes are rejected. | `Game.ranking` | `test_services_games::test_finished_game_is_immutable`, `test_models_views::test_game_view_orders_ranking_and_turns_newest_first` |

## Non-functional requirements (ISO/IEC 25010)

| ID | Quality attribute | Requirement | Verification |
|---|---|---|---|
| RNF-01 | Usability | Usable on phone screens (≥360 px) without horizontal page scroll; wide tables scroll inside their own container. | Manual (Gradio responsive layout + `st-table-wrap`). |
| RNF-02 | Security | Passwords are never stored in plaintext (salted scrypt via Werkzeug). | `test_security::test_hash_is_salted_and_verifiable` |
| RNF-03 | Security | The acting user is taken from the server-side authenticated session, never from browser-supplied fields. | Design review of `ui/app.py::run`; threat T-05. |
| RNF-04 | Maintainability | Business logic is independent of the UI framework (`services/`, `rules.py`, `tiles.py`); rendering is pure. | Module structure; pure tests run without Gradio. |
| RNF-05 | Portability | Runs on Python ≥ 3.11 on Linux/macOS/Windows with no OS-level dependency. | CI matrix (3.11–3.13). |
| RNF-06 | Reliability | Production data survives restarts and redeploys (managed PostgreSQL, ADR-0003). Schema changes need migrations (open item R-05). | `config` refuses production without `DATABASE_URL`: `test_config::test_production_requires_database_url`. |
| RNF-07 | Security | Repeated failed logins for one username are throttled (5 failures / 5 min → 5 min lockout). | `test_security::test_locks_after_max_failures_then_unlocks`, `test_auth::test_lockout_blocks_even_the_correct_password` |
| RNF-08 | Security | All user-controlled text is HTML-escaped in rendered output. | `test_render::*` |
| RNF-09 | Observability | Security and lifecycle events are logged to stdout as `event key=value` lines, safe against log injection. | `test_logging_config::*` |
| RNF-10 | Deployability | Production fails fast on missing or unsafe configuration; the app deploys from `render.yaml`. | `test_config::*`; manual Render deploy. |

## Constraints

| ID | Constraint |
|---|---|
| R-01 | PostgreSQL in production; SQLite only for local development and tests (ADR-0001 superseded by ADR-0003). |
| R-02 | UI framework is Gradio ≥ 6 (ADR-0002); language Python ≥ 3.11. |
| R-03 | PEP 8/257 style enforced by Ruff; type hints on new code, checked by mypy. |
| R-04 | No regulated or sensitive personal data is processed beyond usernames and password hashes. |
| R-05 | Target host is Render; free-tier limits apply (see `docs/DEPLOYMENT.md`). |

## Known limitations of the domain model

- Ties are awarded to the earliest player in turn order when counting wins.
- The Spanish tile table does not model the `RR` digraph (see `docs/RISKS.md`).
- Typing `CH`/`LL` is interpreted as the digraph tile, never as two tiles.
