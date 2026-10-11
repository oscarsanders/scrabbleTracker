# Deployment guide — Render

Reference: SWEBOK v4 KA06 (operations). Facts about Render were checked against
Render's documentation on 2026-10-11; re-verify pricing and limits before you
rely on them.

## 1. What gets deployed

| Resource | Defined in `render.yaml` | Notes |
|---|---|---|
| Web service `scrabble-tracker` | Python runtime, `pip install .`, `python -m scrabble_tracker` | Python version from `.python-version` (3.12). |
| PostgreSQL `scrabble-db` | `plan: free` | **Expires 30 days after creation**, 1 GB, no backups. |

## 2. Free-tier behaviour you must know

- The web service **spins down after 15 minutes without traffic**; the next
  request waits roughly a minute. Users must sign in again after a restart
  (sessions are in memory).
- The filesystem is ephemeral — which is why production requires PostgreSQL.
- Free Postgres: see R-01. **Do not store data you care about on it**; upgrade
  the database plan or point `DATABASE_URL` at another managed Postgres.

## 3. First deployment

1. Push the repository to GitHub.
2. In Render: **New → Blueprint**, pick the repository, confirm `render.yaml`.
3. When prompted, enter `SCRABBLE_ADMIN_PASSWORD` (≥ 8 chars, not `admin1234`).
4. Wait for the build. Open the service URL and sign in as `admin` with that
   password. The admin account is created automatically on first start.
5. In the **Admin** tab, create accounts for your players and give them their
   initial passwords; they can change them in **Profile → Change password**.

Every push to the tracked branch redeploys automatically (`autoDeploy: true`).

## 4. Configuration reference

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `SCRABBLE_ENV` | no | `development` | `production` enables fail-fast validation. |
| `DATABASE_URL` | prod: yes | SQLite `./data/scrabble.db` (dev) | SQLAlchemy URL; `postgres://`/`postgresql://` are normalised. |
| `SCRABBLE_ADMIN_USERNAME` | no | `admin` | Bootstrap admin name. |
| `SCRABBLE_ADMIN_PASSWORD` | prod: yes | dev: `admin1234` | Used **only when the admin account does not exist yet**. Rotate later in the UI. |
| `PORT` | set by Render | `7860` | Listening port. |
| `SCRABBLE_HOST` | no | `0.0.0.0` in prod, `127.0.0.1` otherwise | Bind address. |
| `SCRABBLE_LOG_LEVEL` | no | `INFO` | Log verbosity. |
| `GRADIO_ANALYTICS_ENABLED` | no | `False` in blueprint | Disables Gradio telemetry. |
| `GRADIO_SSR_MODE` | no | `False` in blueprint | Keeps pure client-side rendering (no Node needed). |

Startup errors are explicit, for example *"DATABASE_URL is required in
production"* — read the service logs first.

## 5. Operations

**Logs:** stdout, one line per event, e.g.
`2026-10-11T10:00:00 WARNING [scrabble_tracker.auth] login_failed username='bob'`.
Useful events: `login_failed`, `login_blocked`, `game_created`,
`game_finished`, `user_created`, `user_deleted`, `unhandled_ui_error`.

**Backups** (needed on any plan, the free one has none): with the database's
*external* connection string from the Render dashboard,

```bash
pg_dump "$EXTERNAL_DATABASE_URL" --format=custom --file=scrabble-$(date +%F).dump
# restore into an empty database:
pg_restore --no-owner --dbname "$TARGET_DATABASE_URL" scrabble-YYYY-MM-DD.dump
```

**Moving off the free database:** create/upgrade the database, `pg_dump` the
old one, `pg_restore` into the new one, update `DATABASE_URL` on the web
service, redeploy. If you use an external provider, delete the `databases:`
block and the `fromDatabase` reference from `render.yaml` and set
`DATABASE_URL` manually as a secret.

**Rollback:** redeploy the previous successful commit from the Render
dashboard (or `git revert` and push). Schema is created idempotently; there are
no destructive migrations at this time.

**Locked-out admin / forgotten password:** the bootstrap password is ignored
once the admin exists. Reset by updating `users.password_hash` in the database
with a hash produced by `python -c "from scrabble_tracker.security import
hash_password as h; print(h('NEW-PASSWORD'))"`.

## 6. Run locally

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env            # defaults are fine locally
python -m scrabble_tracker      # http://127.0.0.1:7860, admin / admin1234
```
