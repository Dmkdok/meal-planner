from os import getenv
from raskladka import app, init_db


# Optional DB init controlled by INIT_DB env (default false for prod)
if getenv("INIT_DB", "false").lower() in {"1", "true", "yes"}:
    with app.app_context():
        init_db()

application = app


