from flask import (
    Flask,
    render_template_string,
    request,
    jsonify,
    redirect,
    url_for,
    flash,
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from flask_bcrypt import Bcrypt
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key"  # Замените на безопасный ключ в продакшене
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///meals.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


# Модели
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    meal_plans = db.relationship("MealPlan", backref="user", lazy=True)


class MealPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    days = db.relationship("Day", backref="meal_plan", lazy=True)


class Day(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meal_plan_id = db.Column(db.Integer, db.ForeignKey("meal_plan.id"), nullable=False)
    day_number = db.Column(db.Integer, nullable=False)
    meals = db.relationship("Meal", backref="day", lazy=True)


class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_id = db.Column(db.Integer, db.ForeignKey("day.id"), nullable=False)
    meal_type = db.Column(db.String(50), nullable=False)
    products = db.relationship("Product", backref="meal", lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meal_id = db.Column(db.Integer, db.ForeignKey("meal.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Integer, nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Инициализация базы данных
def init_db():
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Ошибка при создании базы данных: {e}")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if User.query.filter_by(username=username).first():
            flash("Имя пользователя уже занято")
            return redirect(url_for("register"))

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash("Регистрация прошла успешно! Теперь вы можете войти.")
        return redirect(url_for("login"))

    return render_template_string(
        """
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <title>Регистрация</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 400px; margin: 0 auto; padding: 20px; background: white; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
                h1 { text-align: center; color: #2c3e50; }
                input { width: 100%; padding: 8px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
                button { width: 100%; padding: 10px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; }
                button:hover { background: #45a049; }
                .login-link { text-align: center; margin-top: 15px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Регистрация</h1>
                <form method="post">
                    <input type="text" name="username" placeholder="Имя пользователя" required>
                    <input type="password" name="password" placeholder="Пароль" required>
                    <button type="submit">Зарегистрироваться</button>
                </form>
                {% with messages = get_flashed_messages() %}
                    {% if messages %}
                        {% for message in messages %}
                            <p>{{ message }}</p>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                <div class="login-link">
                    <a href="{{ url_for('login') }}">Уже есть аккаунт? Войти</a>
                </div>
            </div>
        </body>
        </html>
    """
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("index"))
        flash("Неверное имя пользователя или пароль")

    return render_template_string(
        """
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <title>Вход</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 400px; margin: 0 auto; padding: 20px; background: white; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
                h1 { text-align: center; color: #2c3e50; }
                input { width: 100%; padding: 8px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
                button { width: 100%; padding: 10px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; }
                button:hover { background: #45a049; }
                .register-link { text-align: center; margin-top: 15px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Вход</h1>
                <form method="post">
                    <input type="text" name="username" placeholder="Имя пользователя" required>
                    <input type="password" name="password" placeholder="Пароль" required>
                    <button type="submit">Войти</button>
                </form>
                {% with messages = get_flashed_messages() %}
                    {% if messages %}
                        {% for message in messages %}
                            <p>{{ message }}</p>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                <div class="register-link">
                    <a href="{{ url_for('register') }}">Нет аккаунта? Зарегистрироваться</a>
                </div>
            </div>
        </body>
        </html>
    """
    )


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        data = request.get_json()
        action = data.get("action")
        selected_plan_id = data.get("plan_id")

        if action == "delete_plan":
            meal_plan = db.session.get(MealPlan, selected_plan_id)
            if meal_plan and meal_plan.user_id == current_user.id:
                db.session.delete(meal_plan)
                db.session.commit()
                return jsonify({"status": "success", "redirect": url_for("index")})
            return jsonify(
                {
                    "status": "error",
                    "message": "Раскладка не найдена или доступ запрещён",
                }
            )

        elif action == "update_plan_name":
            meal_plan = db.session.get(MealPlan, selected_plan_id)
            if meal_plan and meal_plan.user_id == current_user.id:
                meal_plan.name = data["new_name"]
                db.session.commit()
                return jsonify({"status": "success"})
            return jsonify(
                {
                    "status": "error",
                    "message": "Раскладка не найдена или доступ запрещён",
                }
            )

        elif action == "delete_day":
            day = db.session.get(Day, data["day_id"])
            if day and day.meal_plan.user_id == current_user.id:
                db.session.delete(day)
                db.session.commit()
                return jsonify({"status": "success"})
            return jsonify(
                {"status": "error", "message": "День не найден или доступ запрещён"}
            )

        elif action == "update_product":
            product = db.session.get(Product, data["product_id"])
            if product and product.meal.day.meal_plan.user_id == current_user.id:
                product.name = data["name"]
                product.weight = data["weight"]
                db.session.commit()
                return jsonify({"status": "success"})
            return jsonify(
                {"status": "error", "message": "Продукт не найден или доступ запрещён"}
            )

        elif action == "delete_product":
            product = db.session.get(Product, data["product_id"])
            if product and product.meal.day.meal_plan.user_id == current_user.id:
                db.session.delete(product)
                db.session.commit()
                return jsonify({"status": "success"})
            return jsonify(
                {"status": "error", "message": "Продукт не найден или доступ запрещён"}
            )

        elif action == "add_day":
            meal_plan = db.session.get(MealPlan, selected_plan_id)
            if meal_plan and meal_plan.user_id == current_user.id:
                new_day = Day(meal_plan=meal_plan, day_number=data["day_number"])
                db.session.add(new_day)
                db.session.commit()
                return jsonify({"status": "success"})
            return jsonify(
                {
                    "status": "error",
                    "message": "Раскладка не найдена или доступ запрещён",
                }
            )

        elif action == "add_meal":
            meal_plan = db.session.get(MealPlan, selected_plan_id)
            if meal_plan and meal_plan.user_id == current_user.id:
                day = Day.query.filter_by(
                    meal_plan_id=selected_plan_id, day_number=data["day_number"]
                ).first()
                if day:
                    new_meal = Meal(day=day, meal_type=data["meal_type"])
                    db.session.add(new_meal)
                    db.session.commit()
                    return jsonify({"status": "success"})
            return jsonify(
                {"status": "error", "message": "День или раскладка не найдены"}
            )

        elif action == "add_product":
            meal = db.session.get(Meal, data["meal_id"])
            if meal and meal.day.meal_plan.user_id == current_user.id:
                new_product = Product(
                    meal=meal, name=data["name"], weight=data["weight"]
                )
                db.session.add(new_product)
                db.session.commit()
                return jsonify({"status": "success"})
            return jsonify(
                {
                    "status": "error",
                    "message": "Прием пищи не найден или доступ запрещён",
                }
            )

        elif action == "remove_meal":
            meal = db.session.get(Meal, data["meal_id"])
            if meal and meal.day.meal_plan.user_id == current_user.id:
                db.session.delete(meal)
                db.session.commit()
                return jsonify({"status": "success"})
            return jsonify(
                {
                    "status": "error",
                    "message": "Прием пищи не найден или доступ запрещён",
                }
            )

        elif action == "create_plan":
            new_plan = MealPlan(user_id=current_user.id, name=data["name"])
            db.session.add(new_plan)
            db.session.commit()
            return jsonify({"status": "success"})

    meal_plans = MealPlan.query.filter_by(user_id=current_user.id).all()
    selected_plan_id = request.args.get("plan_id")
    selected_plan = (
        db.session.get(MealPlan, selected_plan_id)
        if selected_plan_id
        else meal_plans[0] if meal_plans else None
    )

    if not selected_plan:
        selected_plan = MealPlan(user_id=current_user.id, name="Current Plan")
        day = Day(meal_plan=selected_plan, day_number=1)
        for meal_type in ["Завтрак", "Обед/Перекус", "Ужин"]:
            meal = Meal(day=day, meal_type=meal_type)
            db.session.add(meal)
        db.session.add(day)
        db.session.add(selected_plan)
        db.session.commit()
        meal_plans = [selected_plan]

    template = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Раскладка продуктов</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; color: #333; display: flex; }
        .sidebar { width: 250px; padding: 20px; background: #fff; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-right: 20px; }
        .main-content { flex-grow: 1; max-width: 950px; }
        .day-container { background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .meal { margin: 15px 0; padding: 15px; background: #fafafa; border-radius: 5px; position: relative; }
        .product-list { margin-top: 10px; }
        .product-item { padding: 5px; display: flex; gap: 10px; align-items: center; }
        button { padding: 8px 15px; border: none; border-radius: 5px; background: #4CAF50; color: white; cursor: pointer; transition: background 0.3s; }
        button:hover { background: #45a049; }
        .remove-btn { background: #e74c3c; position: absolute; right: 15px; top: 15px; padding: 5px 10px; }
        .remove-btn:hover { background: #c0392b; }
        input { padding: 5px; border: 1px solid #ddd; border-radius: 4px; margin-right: 10px; }
        h1 { color: #2c3e50; text-align: center; }
        h2 { color: #34495e; margin-bottom: 15px; }
        .auth-links { text-align: right; margin-bottom: 20px; }
        .plan-list { list-style: none; padding: 0; }
        .plan-list li { padding: 10px; cursor: pointer; }
        .plan-list li:hover { background: #f0f0f0; }
        .selected-plan { background: #e0f7fa; }
        .editable:hover { background: #f0f0f0; cursor: pointer; }
        .edit-input { display: none; width: 80%; }
        .showing { display: inline-block; }
        .delete-plan-btn { background: #e74c3c; margin-top: 10px; }
        .delete-day-btn { background: #e74c3c; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h3>Ваши раскладки</h3>
        <ul class="plan-list">
            {% for plan in meal_plans %}
                <li class="{% if plan.id == selected_plan.id %}selected-plan{% endif %}"
                    onclick="selectPlan({{ plan.id }})">
                    {{ plan.name }} ({{ plan.created_at.strftime('%Y-%m-%d') }})
                </li>
            {% endfor %}
        </ul>
        <input type="text" id="new-plan-name" placeholder="Название новой раскладки">
        <button onclick="createPlan()">Создать раскладку</button>
    </div>
    <div class="main-content">
        <div class="auth-links">
            <a href="{{ url_for('logout') }}">Выйти</a>
        </div>
        <h1>
            <span class="editable" id="plan-name" onclick="editPlanName()">
                {{ selected_plan.name }}
            </span>
            <input type="text" class="edit-input" id="plan-name-input"
                   value="{{ selected_plan.name }}">
            <button class="delete-plan-btn" onclick="deletePlan({{ selected_plan.id }})">
                Удалить раскладку
            </button>
        </h1>

        {% for day in selected_plan.days %}
            <div class="day-container" data-day="{{ day.day_number }}">
                <h2>День {{ day.day_number }}
                    <button class="delete-day-btn" onclick="deleteDay({{ day.id }})">
                        Удалить день
                    </button>
                </h2>
                {% for meal in day.meals %}
                    <div class="meal" data-meal-id="{{ meal.id }}">
                        <strong>{{ meal.meal_type }}</strong>
                        <button class="remove-btn" onclick="removeMeal({{ day.day_number }}, {{ meal.id }})">Удалить</button>
                        <div class="product-list">
                            {% for product in meal.products %}
                                <div class="product-item" data-product-id="{{ product.id }}">
                                    <span class="editable" onclick="editProduct(this, {{ product.id }})">
                                        {{ product.name }} - {{ product.weight }}г
                                    </span>
                                    <input type="text" class="edit-input" data-type="name"
                                           value="{{ product.name }}">
                                    <input type="number" class="edit-input" data-type="weight"
                                           value="{{ product.weight }}">
                                    <button onclick="deleteProduct({{ product.id }})">x</button>
                                </div>
                            {% endfor %}
                            <div>
                                <input type="text" class="product-name" placeholder="Продукт">
                                <input type="number" class="product-weight" placeholder="Вес (г)" min="1">
                                <button onclick="addProduct({{ day.day_number }}, {{ meal.id }})">Добавить</button>
                            </div>
                        </div>
                    </div>
                {% endfor %}
                <button onclick="addMeal({{ day.day_number }})">+ Добавить прием пищи</button>
            </div>
        {% endfor %}
        <button onclick="addDay()">+ Добавить день</button>
    </div>

    <script>
        function selectPlan(planId) {
            window.location.href = `/?plan_id=${planId}`;
        }

        function editPlanName() {
            const span = document.getElementById('plan-name');
            const input = document.getElementById('plan-name-input');
            span.style.display = 'none';
            input.classList.add('showing');
            input.focus();
            input.onblur = async () => {
                const newName = input.value;
                await fetch('/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        action: 'update_plan_name',
                        plan_id: {{ selected_plan.id }},
                        new_name: newName
                    })
                });
                span.textContent = newName;
                span.style.display = 'inline';
                input.classList.remove('showing');
            };
        }

        async function deletePlan(planId) {
            if (confirm('Вы уверены, что хотите удалить раскладку?')) {
                const response = await fetch('/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'delete_plan', plan_id: planId })
                });
                const data = await response.json();
                if (data.status === 'success') {
                    window.location.href = data.redirect;
                }
            }
        }

        async function deleteDay(dayId) {
            if (confirm('Вы уверены, что хотите удалить день?')) {
                try {
                    const response = await fetch('/', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ action: 'delete_day', day_id: dayId })
                    });
                    const data = await response.json();
                    if (data.status === 'success') {
                        location.reload();
                    } else {
                        console.error('Ошибка удаления дня:', data);
                        alert('Не удалось удалить день');
                    }
                } catch (error) {
                    console.error('Ошибка при запросе:', error);
                    alert('Произошла ошибка при удалении дня');
                }
            }
        }

        function editProduct(element, productId) {
            const productDiv = element.parentElement;
            const span = element;
            const nameInput = productDiv.querySelector('input[data-type="name"]');
            const weightInput = productDiv.querySelector('input[data-type="weight"]');

            span.style.display = 'none';
            nameInput.classList.add('showing');
            weightInput.classList.add('showing');
            nameInput.focus();

            const saveChanges = async () => {
                await fetch('/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        action: 'update_product',
                        product_id: productId,
                        name: nameInput.value,
                        weight: weightInput.value
                    })
                });
                span.textContent = `${nameInput.value} - ${weightInput.value}г`;
                span.style.display = 'inline';
                nameInput.classList.remove('showing');
                weightInput.classList.remove('showing');
            };

            nameInput.onblur = saveChanges;
            weightInput.onblur = saveChanges;
        }

        async function deleteProduct(productId) {
            if (confirm('Удалить продукт?')) {
                await fetch('/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'delete_product', product_id: productId })
                });
                location.reload();
            }
        }

        async function addDay() {
            const days = document.querySelectorAll('.day-container');
            const newDayNumber = days.length + 1;
            await fetch('/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action: 'add_day',
                    plan_id: {{ selected_plan.id }},
                    day_number: newDayNumber
                })
            });
            location.reload();
        }

        async function addMeal(dayNumber) {
            const mealType = prompt('Введите тип приема пищи (например, Завтрак):');
            if (mealType) {
                await fetch('/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        action: 'add_meal',
                        plan_id: {{ selected_plan.id }},
                        day_number: dayNumber,
                        meal_type: mealType
                    })
                });
                location.reload();
            }
        }

        async function addProduct(dayNumber, mealId) {
            const productNameInput = document.querySelector(`.meal[data-meal-id="${mealId}"] .product-name`);
            const productWeightInput = document.querySelector(`.meal[data-meal-id="${mealId}"] .product-weight`);
            const name = productNameInput.value;
            const weight = productWeightInput.value;

            if (name && weight) {
                await fetch('/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        action: 'add_product',
                        meal_id: mealId,
                        name: name,
                        weight: weight
                    })
                });
                location.reload();
            }
        }

        async function removeMeal(dayNumber, mealId) {
            if (confirm('Удалить прием пищи?')) {
                await fetch('/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        action: 'remove_meal',
                        meal_id: mealId
                    })
                });
                location.reload();
            }
        }

        async function createPlan() {
            const newPlanName = document.getElementById('new-plan-name').value;
            if (newPlanName) {
                await fetch('/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        action: 'create_plan',
                        name: newPlanName
                    })
                });
                location.reload();
            }
        }
    </script>
</body>
</html>"""
    return render_template_string(
        template, meal_plans=meal_plans, selected_plan=selected_plan
    )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
