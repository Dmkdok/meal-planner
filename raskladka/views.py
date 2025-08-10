# raskladka/views.py
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from raskladka import db, bcrypt
from raskladka.models import User, MealPlan, Day, Meal, Product

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
                meal_plan = db.session.get(MealPlan, selected_plan_id)
                if meal_plan and meal_plan.user_id == current_user.id:
                    db.session.delete(meal_plan)
                    db.session.commit()
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

        elif action == "update_meal_name":
            meal = db.session.get(Meal, data["meal_id"])
            if meal and meal.day.meal_plan.user_id == current_user.id:
                meal.meal_type = data["meal_name"]
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

    return render_template(
        "index.html", meal_plans=meal_plans, selected_plan=selected_plan
    )


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
