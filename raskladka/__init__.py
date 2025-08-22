# raskladka/__init__.py
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///meals.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "views.login"

from raskladka.models import User
from raskladka.views import views

app.register_blueprint(views)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def init_db():
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Ошибка при создании базы данных: {e}")


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
