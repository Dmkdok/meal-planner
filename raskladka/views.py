# raskladka/views.py
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from raskladka import db, bcrypt
from raskladka.models import User, MealPlan, Day, Meal, Product
from raskladka.services import (
    CalculationService,
    MealPlanService,
    DayService,
    MealService,
    ProductService,
)
from raskladka.utils import validate_positive_integer

views = Blueprint("views", __name__)


@views.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("views.index"))
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if User.query.filter_by(username=username).first():
            flash("Имя пользователя уже занято")
            return redirect(url_for("views.register"))

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash("Регистрация прошла успешно! Теперь вы можете войти.")
        return redirect(url_for("views.login"))

    return render_template("register.html")


@views.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("views.index"))
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("views.index"))
        flash("Неверное имя пользователя или пароль")

    return render_template("login.html")


@views.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        data = request.get_json()
        action = data.get("action")
        selected_plan_id = data.get("plan_id")

        if action == "delete_plan":
            try:
                success = MealPlanService.delete_plan(selected_plan_id, current_user.id)
                if success:
                    return jsonify(
                        {"status": "success", "redirect": url_for("views.index")}
                    )
                else:
                    return jsonify(
                        {
                            "status": "error",
                            "message": "Раскладка не найдена или доступ запрещён",
                        }
                    )
            except Exception as e:
                db.session.rollback()
                print(f"Ошибка при удалении раскладки: {e}")
                return jsonify(
                    {
                        "status": "error",
                        "message": f"Ошибка при удалении раскладки: {str(e)}",
                    }
                )

        elif action == "update_plan_name":
            success = MealPlanService.update_plan_name(
                selected_plan_id, current_user.id, data["new_name"]
            )
            if success:
                return jsonify({"status": "success"})
            return jsonify(
                {
                    "status": "error",
                    "message": "Раскладка не найдена или доступ запрещён",
                }
            )

        elif action == "delete_day":
            success = DayService.delete_day(data["day_id"], current_user.id)
            if success:
                return jsonify({"status": "success"})
            return jsonify(
                {"status": "error", "message": "День не найден или доступ запрещён"}
            )

        elif action == "update_product":
            success, message = ProductService.update_product(
                data["product_id"], current_user.id, data["name"], data["weight"]
            )
            if success:
                return jsonify({"status": "success"})
            return jsonify(
                {"status": "error", "message": message}
            )

        elif action == "delete_product":
            success = ProductService.delete_product(data["product_id"], current_user.id)
            if success:
                return jsonify({"status": "success"})
            return jsonify(
                {"status": "error", "message": "Продукт не найден или доступ запрещён"}
            )

        elif action == "add_day":
            success = DayService.add_day(
                selected_plan_id, current_user.id, data["day_number"]
            )
            if success:
                return jsonify({"status": "success"})
            return jsonify(
                {
                    "status": "error",
                    "message": "Раскладка не найдена или доступ запрещён",
                }
            )

        elif action == "add_meal":
            success = MealService.add_meal(
                selected_plan_id, current_user.id, data["day_number"], data["meal_type"]
            )
            if success:
                return jsonify({"status": "success"})
            return jsonify(
                {"status": "error", "message": "День или раскладка не найдены"}
            )

        elif action == "add_product":
            success, message = ProductService.add_product(
                data["meal_id"], current_user.id, data["name"], data["weight"]
            )
            if success:
                return jsonify({"status": "success"})
            return jsonify(
                {
                    "status": "error",
                    "message": message,
                }
            )

        elif action == "remove_meal":
            success = MealService.delete_meal(data["meal_id"], current_user.id)
            if success:
                return jsonify({"status": "success"})
            return jsonify(
                {
                    "status": "error",
                    "message": "Прием пищи не найден или доступ запрещён",
                }
            )

        elif action == "update_meal_name":
            success = MealService.update_meal_type(
                data["meal_id"], current_user.id, data["meal_name"]
            )
            if success:
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

    meal_plans = MealPlanService.get_user_plans(current_user.id)
    selected_plan_id = request.args.get("plan_id")
    selected_plan = (
        MealPlanService.get_plan_by_id(selected_plan_id, current_user.id)
        if selected_plan_id
        else meal_plans[0]
        if meal_plans
        else None
    )

    if not selected_plan:
        selected_plan = MealPlanService.create_default_plan(current_user.id)
        meal_plans = [selected_plan]

    return render_template(
        "index.html", meal_plans=meal_plans, selected_plan=selected_plan
    )


@views.route("/calculate", methods=["POST"])
@login_required
def calculate_products():
    """API endpoint для расчета продуктов на основе раскладки"""
    try:
        data = request.get_json()
        plan_id = data.get("plan_id")
        trip_days = data.get("trip_days")
        people_count = data.get("people_count")

        if not all([plan_id, trip_days, people_count]):
            return jsonify(
                {
                    "status": "error",
                    "message": "Необходимо указать plan_id, trip_days и people_count",
                }
            ), 400

        # Валидация входных данных
        is_valid_trip_days, trip_days_error = validate_positive_integer(
            trip_days, "Количество дней похода"
        )
        if not is_valid_trip_days:
            return jsonify({"status": "error", "message": trip_days_error}), 400

        is_valid_people_count, people_count_error = validate_positive_integer(
            people_count, "Количество человек"
        )
        if not is_valid_people_count:
            return jsonify({"status": "error", "message": people_count_error}), 400

        # Получаем план питания
        meal_plan = MealPlanService.get_plan_by_id(plan_id, current_user.id)
        if not meal_plan:
            return jsonify(
                {
                    "status": "error",
                    "message": "Раскладка не найдена или доступ запрещён",
                }
            ), 404

        # Выполняем расчет
        result = CalculationService.calculate_products_from_layout(
            meal_plan, trip_days, people_count
        )

        if not result.get("success"):
            return jsonify(
                {"status": "error", "message": result.get("error", "Ошибка расчета")}
            ), 400

        return jsonify({"status": "success", "data": result})

    except Exception as e:
        print(f"Ошибка при расчете продуктов: {e}")
        return jsonify({"status": "error", "message": "Внутренняя ошибка сервера"}), 500


@views.route("/day/<int:day_id>/edit")
@login_required
def edit_day(day_id):
    day = db.session.get(Day, day_id)
    if not day or day.meal_plan.user_id != current_user.id:
        flash("День не найден или доступ запрещён")
        return redirect(url_for("views.index"))

    return render_template("edit_day.html", day=day, meal_plan=day.meal_plan)


@views.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("views.login"))
