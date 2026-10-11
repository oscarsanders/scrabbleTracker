# Deployment guide — Render (stateless edition)

Facts about Render were checked against its documentation on 2026-10-11;
re-verify limits before relying on them.

The app needs **no database, no secrets and no environment variables**.

## Option A — Blueprint (recommended)

1. Push the repository to GitHub (files must sit in the repo **root**:
   `pyproject.toml`, `render.yaml`, `src/`).
2. Render → **New → Blueprint** → select the repo → **Apply**.

## Option B — Manual Web Service

| Field | Value |
|---|---|
| Runtime / Language | Python 3 |
| Build Command | `pip install .` |
| Start Command | `python -m scrabble_tracker` |
| Instance type | Free |

> If you leave the default Build Command, Render may pick `poetry install`
> because `pyproject.toml` exists, and the build fails. Always set
> `pip install .`.

Environment variables are optional. If you created the service for the previous
version you can delete `SCRABBLE_ENV`, `DATABASE_URL`,
`SCRABBLE_ADMIN_PASSWORD` and `SCRABBLE_ADMIN_USERNAME`; they are ignored.

| Optional variable | Purpose |
|---|---|
| `PYTHON_VERSION` | e.g. `3.12.8` to pin Python. Render's default (3.14) also works with Gradio 6. |
| `SCRABBLE_LOG_LEVEL` | `DEBUG`, `INFO` (default), `WARNING`. |

## Behaviour to expect

- The free instance **sleeps after ~15 min without traffic**; waking takes about
  a minute. Any game in progress is lost (R-02).
- Reloading the page discards your game; use **Start a new game** to reset.
- Logs (Render → Logs) show one line at startup, for example
  `starting version='3.0.0' host='0.0.0.0' port=10000`.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `The Poetry configuration is invalid` | Build Command is `poetry install`; set `pip install .`. |
| `No open ports detected on 0.0.0.0` | Old version of the code is running (it listened on loopback). Redeploy the latest commit; this edition binds `0.0.0.0:$PORT` automatically. |
| Build fails installing Gradio | Set `PYTHON_VERSION` to `3.12.8` and redeploy. |
| Page loads but buttons do nothing | Open the browser console and the Render logs and report the error (R-03). |

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m scrabble_tracker                          # http://127.0.0.1:7860
```
