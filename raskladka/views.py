# raskladka/views.py
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file
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
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

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


@views.route("/export_excel", methods=["GET"])
@login_required
def export_excel():
    """Экспорт таблицы расчета в Excel"""
    try:
        plan_id = request.args.get("plan_id")
        trip_days = request.args.get("trip_days")
        people_count = request.args.get("people_count")

        if not all([plan_id, trip_days, people_count]):
            return jsonify({
                "status": "error",
                "message": "Необходимо указать plan_id, trip_days и people_count"
            }), 400

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

        trip_days = int(trip_days)
        people_count = int(people_count)

        # Получаем план питания и проверяем доступ
        meal_plan = MealPlanService.get_plan_by_id(plan_id, current_user.id)
        if not meal_plan:
            return jsonify({
                "status": "error",
                "message": "Раскладка не найдена или доступ запрещён",
            }), 404

        # Рассчитываем данные
        calc_result = CalculationService.calculate_products_from_layout(
            meal_plan, trip_days, people_count
        )
        if not calc_result.get("success"):
            return jsonify({
                "status": "error",
                "message": calc_result.get("error", "Ошибка расчета"),
            }), 400

        results = calc_result["results"]
        summary = calc_result["summary"]
        meal_types_by_day = calc_result["meal_types_by_day"]
        product_meal_usage = calc_result["product_meal_usage"]

        layout_days_count = summary["layout_days_count"]

        # Создаем Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "Расчет"

        # Стили
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="667EEA", end_color="667EEA", fill_type="solid")
        thin_border = Border(left=Side(style="thin", color="DDDDDD"),
                             right=Side(style="thin", color="DDDDDD"),
                             top=Side(style="thin", color="DDDDDD"),
                             bottom=Side(style="thin", color="DDDDDD"))

        # Заголовки
        headers = [
            "Продукт",
            f"1 прием пищи на {people_count} чел.",
        ]

        # Заголовки для каждого рациона
        for i in range(layout_days_count):
            day_meal_types = meal_types_by_day[i] if i < len(meal_types_by_day) else []
            meal_type_text = ", ".join(day_meal_types) if day_meal_types else f"Рацион {i + 1}"
            headers.append(f"Рацион {i + 1}\n{meal_type_text}")

        headers.extend([
            "Количество повторений",
            "Общий вес для покупки",
        ])

        ws.append(headers)
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin_border

        # Данные
        for item in results:
            name = item.get("name", "")
            weight_per_meal = item.get("weight_per_meal", 0) or 0
            weight_per_meal_for_people = weight_per_meal * people_count

            row = [name, round(weight_per_meal_for_people, 2)]

            total_occurrences = 0
            usage_map = product_meal_usage.get(name, {})

            for i in range(layout_days_count):
                usage_count = usage_map.get(i, 0)
                # Сколько раз используется рацион с индексом i в пределах trip_days
                if i >= trip_days:
                    repetitions_for_ration = 0
                else:
                    repetitions_for_ration = ((trip_days - 1 - i) // layout_days_count) + 1
                total_usage_for_ration = usage_count * repetitions_for_ration
                total_occurrences += total_usage_for_ration
                row.append(total_usage_for_ration if total_usage_for_ration > 0 else "")

            total_weight = round(total_occurrences * weight_per_meal_for_people, 2)
            row.extend([total_occurrences, total_weight])

            ws.append(row)

        # Применяем границы и выравнивание для всех данных
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
            for cell in row:
                cell.border = thin_border
                align = "left" if cell.column == 1 else "center"
                cell.alignment = Alignment(horizontal=align, vertical="center")

        # Устанавливаем ширину столбцов
        column_widths = {}
        for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
            for cell in row:
                value = str(cell.value) if cell.value is not None else ""
                column_widths[cell.column_letter] = max(column_widths.get(cell.column_letter, 0), len(value) + 2)

        for col_letter, width in column_widths.items():
            ws.column_dimensions[col_letter].width = min(40, width)

        # Итоговая строка (сумма общего веса)
        if ws.max_row >= 2:
            sum_cell = f"=SUM({ws.cell(row=2, column=ws.max_column).coordinate}:{ws.cell(row=ws.max_row, column=ws.max_column).coordinate})"
            ws.append(["ИТОГО", "", *([""] * (layout_days_count)), "", sum_cell])
            last_row = ws.max_row
            for cell in ws[last_row]:
                cell.border = thin_border
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center", vertical="center")

        # Отдаем файл
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        safe_name = meal_plan.name.replace("/", "-").replace("\\", "-")
        filename = f"{safe_name} - расчет.xlsx"

        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except Exception as e:
        print(f"Ошибка при экспорте Excel: {e}")
        return jsonify({"status": "error", "message": "Внутренняя ошибка сервера"}), 500
