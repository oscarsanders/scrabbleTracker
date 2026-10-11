# Risk register

Probability (P) and impact (I): L/M/H. Owner: maintainer. Review at every release.

| ID | Risk | P | I | Mitigation / trigger |
|---|---|---|---|---|
| R-01 | **Free Render PostgreSQL expires 30 days after creation** (14-day grace, no backups). All data lost if ignored. | H | H | Before keeping real data: upgrade the DB plan or use an external Postgres (`docs/DEPLOYMENT.md`). Take `pg_dump` backups. |
| R-02 | **Gradio API drift** between minor versions (v6 already changed `theme`/`css`/`api_name`). | M | M | Bounded `<7.0`; UI smoke test; review Dependabot PRs; ADR-0002. |
| R-03 | Free web service spins down after 15 min idle (≈1 min cold start) and loses in-memory sessions and throttle state. | H | L | Documented; paid instance removes spin-down. |
| R-04 | No dependency lock file → builds are not bit-for-bit reproducible. | M | M | Generate one with `uv pip compile` or `pip-compile` once network access to PyPI is available, commit it and install from it on Render. |
| R-05 | `create_all` does not alter existing tables; a model change would not reach an existing production DB. | M | H | Introduce Alembic **before the first schema change**; until then, schema is frozen. |
| R-06 | Login throttling is in-memory and per process; a second instance would not share it. | L | M | Keep one instance, or move state to the database/Redis if scaled. |
| R-07 | **Initial verification gap:** the v2 migration was authored in an environment without Gradio, SQLAlchemy or network. Pure-logic tests (43 cases) were executed; DB- and Gradio-dependent tests and the UI were reviewed but **not executed** by the author. | M | M | Run `pytest` and a manual smoke test (below) before the first production deploy; fix findings. |
| R-08 | Spanish tile table lacks the `RR` digraph (verify against the official Spanish set before relying on Spanish end-of-game scoring with `RR`). | M | L | Add to `tiles.py` with a test once confirmed. |

## Manual smoke test (R-07)

1. `pip install -e ".[dev]" && pytest` → all green.
2. `python -m scrabble_tracker`, open the printed URL, sign in as `admin`.
3. Admin tab: create `bob`. Log out, sign in as `bob`.
4. New game (multiplayer, "Guest Gina"), add several moves incl. foul/pass, undo one.
5. Finish with one empty rack: check bonus/penalty and ranking.
6. History, Profile and *Change password* work; Admin tab is inert for `bob`.
