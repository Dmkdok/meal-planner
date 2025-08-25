from pathlib import Path
import os
from alembic.config import Config
from alembic import command
from raskladka import app


def _upgrade_db() -> None:
    ini_path = Path(__file__).resolve().parents[1] / "alembic.ini"
    cfg = Config(str(ini_path))
    # Ensure script location is correct when running from packaged image
    cfg.set_main_option(
        "script_location",
        str(Path(__file__).resolve().parents[1] / "migrations"),
    )
    # Pass actual DB URL from Flask config
    cfg.set_main_option(
        "sqlalchemy.url", app.config["SQLALCHEMY_DATABASE_URI"]
    )
    command.upgrade(cfg, "head")


# Run migrations on startup only if INIT_DB=true
if os.environ.get("INIT_DB", "false").lower() in (
    "1",
    "true",
    "yes",
):  # noqa: PIE807
    try:
        _upgrade_db()
    except Exception:  # noqa: BLE001
        # Avoid crashing Gunicorn workers on failed migration; log and continue
        import traceback

        print("[wsgi] Alembic upgrade failed during startup", flush=True)
        traceback.print_exc()

application = app
