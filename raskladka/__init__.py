# raskladka/__init__.py
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
import os
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "your-secret-key")

# Database URI
_db_uri = os.environ.get("DATABASE_URI", "sqlite:///meals.db")
app.config["SQLALCHEMY_DATABASE_URI"] = _db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_SECURE"] = os.environ.get(
    "SESSION_COOKIE_SECURE",
    "1",
) in ("1", "true", "yes")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = os.environ.get(
    "SESSION_COOKIE_SAMESITE",
    "Lax",
)
app.config["REMEMBER_COOKIE_SECURE"] = app.config["SESSION_COOKIE_SECURE"]
app.config["MAX_CONTENT_LENGTH"] = int(
    os.environ.get("MAX_CONTENT_LENGTH", 10 * 1024 * 1024)
)

# For Postgres (psycopg3), disable server-side prepares and enable pre-ping
if _db_uri.startswith("postgresql"):
    engine_opts = dict(app.config.get("SQLALCHEMY_ENGINE_OPTIONS", {}))
    connect_args = dict(engine_opts.get("connect_args", {}))
    # Disable server-side prepares to avoid duplicate statements
    connect_args.setdefault("prepare_threshold", None)
    engine_opts["connect_args"] = connect_args
    engine_opts.setdefault("pool_pre_ping", True)
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_opts

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "views.login"

from raskladka.models import User
from raskladka.views import views

app.register_blueprint(views)

# Trust proxy headers (for correct scheme/host when behind reverse proxy)
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1
)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def init_db():
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Ошибка при создании базы данных: {e}")


# Ensure DB session cleanup per request
@app.teardown_request
def _teardown_request(exception):  # noqa: D401, ANN001
    """Rollback on exception and remove the session at request end."""
    try:
        if exception is not None:
            db.session.rollback()
    finally:
        db.session.remove()


# Simple health endpoint
@app.get("/health")
def health():  # noqa: D401, ANN001
    """Return health status for container orchestrator."""
    try:
        # simple DB check
        db.session.execute(db.select(1))
        return {"status": "ok"}, 200
    except Exception:
        return {"status": "degraded"}, 500


# ----- Error handlers -----
@app.errorhandler(400)
def handle_400(error):  # noqa: ARG001
    return (
        render_template(
            "errors/error.html",
            code=400,
            title="Некорректный запрос",
            headline="Некорректный запрос",
            description=(
                "Проверьте корректность введённых данных "
                "или попробуйте выполнить "
                "действие заново."
            ),
        ),
        400,
    )


@app.errorhandler(403)
def handle_403(error):  # noqa: ARG001
    return (
        render_template(
            "errors/error.html",
            code=403,
            title="Доступ запрещён",
            headline="Доступ запрещён",
            description=(
                "У вас нет прав для доступа к этой странице. Если это ошибка, "
                "войдите под другим аккаунтом."
            ),
        ),
        403,
    )


@app.errorhandler(404)
def handle_404(error):  # noqa: ARG001
    return (
        render_template(
            "errors/error.html",
            code=404,
            title="Страница не найдена",
            headline="Страница не найдена",
            description=(
                "Такой страницы здесь нет. Возможно, она была перемещена или "
                "адрес введён с ошибкой."
            ),
        ),
        404,
    )


@app.errorhandler(500)
def handle_500(error):  # noqa: ARG001
    return (
        render_template(
            "errors/error.html",
            code=500,
            title="Внутренняя ошибка сервера",
            headline="Что-то пошло не так",
            description=(
                "Мы уже работаем над этим. Попробуйте обновить страницу или "
                "вернуться позже."
            ),
        ),
        500,
    )
