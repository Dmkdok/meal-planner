# raskladka/services.py
from typing import List, Dict, Any, Optional
from datetime import datetime
from raskladka.models import MealPlan, Day, Meal, Product, UserPlanSettings
from raskladka.utils import (
    normalize_product_name_display,
    canonical_product_key,
    validate_product_name,
)


class CalculationService:
    """Сервис для расчета продуктов на основе раскладки"""

    @staticmethod
    def _build_products_map(meal_plan: MealPlan) -> Dict[str, Dict[str, Any]]:
        """
        Собирает продукты, объединяя по каноническому ключу.
        Возвращает словарь:
        canonical_key -> {display_name, weight, occurrences, meal_types}
        """
        products_map: Dict[str, Dict[str, Any]] = {}

        for day in meal_plan.days:
            for meal in day.meals:
                for product in meal.products:
                    key = canonical_product_key(product.name)
                    display_name = normalize_product_name_display(product.name)
                    product_weight = product.weight

                    if key in products_map:
                        products_map[key]["weight"] += product_weight
                        products_map[key]["occurrences"] += 1
                        meal_types = products_map[key]["meal_types"]
                        if meal.meal_type not in meal_types:
                            meal_types.append(meal.meal_type)
                    else:
                        products_map[key] = {
                            "display_name": display_name,
                            "weight": product_weight,
                            "occurrences": 1,
                            "meal_types": [meal.meal_type],
                        }
        return products_map

    @staticmethod
    def _build_meal_usage(
        meal_plan: MealPlan,
        products_map: Dict[str, Dict[str, Any]],
    ) -> tuple[list[list[str]], Dict[str, Dict[int, int]]]:
        """
        Собирает информацию о типах приемов пищи по дням и карту использования
        продуктов (по отображаемым именам).
        """
        meal_types_by_day: list[list[str]] = []
        product_meal_usage: Dict[str, Dict[int, int]] = {}

        for day_index, day in enumerate(meal_plan.days):
            day_meal_types: list[str] = []
            for meal in day.meals:
                if meal.products:
                    day_meal_types.append(meal.meal_type)

                for product in meal.products:
                    key = canonical_product_key(product.name)
                    display_name = (
                        products_map[key]["display_name"]
                        if key in products_map
                        else normalize_product_name_display(product.name)
                    )
                    if display_name not in product_meal_usage:
                        product_meal_usage[display_name] = {}
                    usage_for_day = product_meal_usage[display_name]
                    usage_for_day[day_index] = (
                        usage_for_day.get(day_index, 0) + 1
                    )

            meal_types_by_day.append(day_meal_types)

        return meal_types_by_day, product_meal_usage

    @staticmethod
    def calculate_products_from_layout(
        meal_plan: MealPlan, trip_days: int, people_count: int
    ) -> Dict[str, Any]:
        """
        Рассчитывает необходимое количество продуктов для похода

        Args:
            meal_plan: План питания
            trip_days: Количество дней похода
            people_count: Количество человек

        Returns:
            Словарь с результатами расчета
        """
        if not meal_plan.days:
            return {"error": "В раскладке нет дней", "success": False}

        products_map = CalculationService._build_products_map(meal_plan)
        if not products_map:
            return {"error": "В раскладке нет продуктов", "success": False}

        layout_days_count = len(meal_plan.days)
        layout_repetitions = (
            trip_days + layout_days_count - 1
        ) // layout_days_count
        actual_days_used = layout_repetitions * layout_days_count

        results = []
        for key, product_data in products_map.items():
            total_weight = (
                product_data["weight"] * layout_repetitions * people_count
            )
            total_occurrences = (
                product_data["occurrences"] * layout_repetitions
            )
            weight_per_meal = (
                product_data["weight"] / product_data["occurrences"]
                if product_data["occurrences"] > 0
                else 0
            )

            results.append(
                {
                    "name": product_data["display_name"],
                    "weight": total_weight,
                    "occurrences": total_occurrences,
                    "weight_per_meal": weight_per_meal,
                    "meal_types": product_data["meal_types"],
                    "unit": "г",
                }
            )

        results.sort(key=lambda x: x["weight"], reverse=True)

        meal_types_by_day, product_meal_usage = (
            CalculationService._build_meal_usage(meal_plan, products_map)
        )

        total_weight = sum(result["weight"] for result in results)

        return {
            "success": True,
            "results": results,
            "summary": {
                "trip_days": trip_days,
                "people_count": people_count,
                "layout_days_count": layout_days_count,
                "layout_repetitions": layout_repetitions,
                "actual_days_used": actual_days_used,
                "total_products": len(results),
                "total_weight": total_weight,
            },
            "meal_types_by_day": meal_types_by_day,
            "product_meal_usage": product_meal_usage,
        }


class MealPlanService:
    """Сервис для работы с планами питания"""

    @staticmethod
    def create_default_plan(
        user_id: int, name: str = "Current Plan"
    ) -> MealPlan:
        """Создает план питания с дефолтными данными"""
        from raskladka import db

        meal_plan = MealPlan(user_id=user_id, name=name)
        day = Day(meal_plan=meal_plan, day_number=1)

        # Создаем дефолтные приемы пищи
        for meal_type in ["Завтрак", "Обед/Перекус", "Ужин"]:
            meal = Meal(day=day, meal_type=meal_type)
            db.session.add(meal)

        db.session.add(day)
        db.session.add(meal_plan)
        db.session.commit()

        return meal_plan

    @staticmethod
    def get_user_plans(user_id: int) -> List[MealPlan]:
        """Получает все планы пользователя"""
        return MealPlan.query.filter_by(user_id=user_id).all()

    @staticmethod
    def get_plan_by_id(plan_id: int, user_id: int) -> MealPlan:
        """Получает план по ID с проверкой принадлежности пользователю"""
        return MealPlan.query.filter_by(
            id=plan_id, user_id=user_id
        ).first()

    @staticmethod
    def delete_plan(plan_id: int, user_id: int) -> bool:
        """Удаляет план питания"""
        from raskladka import db

        meal_plan = MealPlan.query.filter_by(
            id=plan_id, user_id=user_id
        ).first()
        if meal_plan:
            db.session.delete(meal_plan)
            db.session.commit()
            return True
        return False

    @staticmethod
    def update_plan_name(plan_id: int, user_id: int, new_name: str) -> bool:
        """Обновляет название плана питания"""
        from raskladka import db

        meal_plan = MealPlan.query.filter_by(
            id=plan_id, user_id=user_id
        ).first()
        if meal_plan:
            meal_plan.name = new_name
            db.session.commit()
            return True
        return False


class DayService:
    """Сервис для работы с днями"""

    @staticmethod
    def add_day(plan_id: int, user_id: int, day_number: int) -> bool:
        """Добавляет новый день в план"""
        from raskladka import db

        meal_plan = MealPlan.query.filter_by(
            id=plan_id,
            user_id=user_id,
        ).first()
        if meal_plan:
            new_day = Day(meal_plan=meal_plan, day_number=day_number)
            db.session.add(new_day)
            db.session.commit()
            return True
        return False

    @staticmethod
    def delete_day(day_id: int, user_id: int) -> bool:
        """Удаляет день"""
        from raskladka import db

        day = (
            Day.query.join(MealPlan)
            .filter(Day.id == day_id, MealPlan.user_id == user_id)
            .first()
        )

        if day:
            db.session.delete(day)
            db.session.commit()
            return True
        return False


class MealService:
    """Сервис для работы с приемами пищи"""

    @staticmethod
    def add_meal(
        plan_id: int, user_id: int, day_number: int, meal_type: str
    ) -> bool:
        """Добавляет новый прием пищи"""
        from raskladka import db

        meal_plan = MealPlan.query.filter_by(
            id=plan_id,
            user_id=user_id,
        ).first()
        if meal_plan:
            day = Day.query.filter_by(
                meal_plan_id=plan_id,
                day_number=day_number,
            ).first()
            if day:
                new_meal = Meal(day=day, meal_type=meal_type)
                db.session.add(new_meal)
                db.session.commit()
                return True
        return False

    @staticmethod
    def delete_meal(meal_id: int, user_id: int) -> bool:
        """Удаляет прием пищи"""
        from raskladka import db

        meal = (
            Meal.query.join(Day)
            .join(MealPlan)
            .filter(
                Meal.id == meal_id,
                MealPlan.user_id == user_id,
            )
            .first()
        )

        if meal:
            db.session.delete(meal)
            db.session.commit()
            return True
        return False

    @staticmethod
    def update_meal_type(meal_id: int, user_id: int, meal_type: str) -> bool:
        """Обновляет тип приема пищи"""
        from raskladka import db

        meal = (
            Meal.query.join(Day)
            .join(MealPlan)
            .filter(Meal.id == meal_id, MealPlan.user_id == user_id)
            .first()
        )

        if meal:
            meal.meal_type = meal_type
            db.session.commit()
            return True
        return False


class ProductService:
    """Сервис для работы с продуктами"""

    @staticmethod
    def validate_product_name_weight(
        user_id: int,
        name: str,
        weight: int,
        exclude_product_id: int = None,
    ) -> tuple[bool, str]:
        """
        Валидирует, что продукты с одинаковым именем имеют одинаковый вес.
        Сравнение имени выполняется без учета регистра и лишних пробелов.
        """
        normalized_display = normalize_product_name_display(name)
        key = canonical_product_key(name)

        query = (
            Product.query.join(Meal)
            .join(Day)
            .join(MealPlan)
            .filter(MealPlan.user_id == user_id)
        )
        if exclude_product_id:
            query = query.filter(
                Product.id != exclude_product_id
            )
        existing_products = query.all()

        for product in existing_products:
            if canonical_product_key(product.name) == key:
                if product.weight != weight:
                    error_msg = (
                        "Продукт '"
                        + normalized_display
                        + "' уже существует с весом "
                        + str(product.weight)
                        + "г. Для добавления продукта с другим весом "
                        + "используйте другое название (например, '"
                        + normalized_display
                        + " утро' или '"
                        + normalized_display
                        + " вечер')."
                    )
                    return False, error_msg

        return True, ""

    @staticmethod
    def add_product(
        meal_id: int, user_id: int, name: str, weight: int
    ) -> tuple[bool, str]:
        """Добавляет новый продукт"""
        from raskladka import db

        # Серверная валидация веса: 1..500_000 г
        if weight < 1:
            return False, "Вес продукта должен быть не меньше 1 грамма"
        if weight > 500_000:
            return False, (
                "Вес продукта должен быть не больше 500 000 г (500 кг)"
            )

        # Серверная валидация названия по регулярному выражению
        ok_name, name_error = validate_product_name(name)
        if not ok_name:
            return False, name_error

        display_name = normalize_product_name_display(name)

        is_valid, error_message = ProductService.validate_product_name_weight(
            user_id, display_name, weight
        )
        if not is_valid:
            return False, error_message

        meal = (
            Meal.query.join(Day)
            .join(MealPlan)
            .filter(Meal.id == meal_id, MealPlan.user_id == user_id)
            .first()
        )

        if meal:
            new_product = Product(meal=meal, name=display_name, weight=weight)
            db.session.add(new_product)
            db.session.commit()
            return True, ""
        return False, "Прием пищи не найден или доступ запрещён"

    @staticmethod
    def update_product(
        product_id: int, user_id: int, name: str, weight: int
    ) -> tuple[bool, str]:
        """Обновляет продукт"""
        from raskladka import db

        # Серверная валидация веса: 1..500_000 г
        if weight < 1:
            return False, "Вес продукта должен быть не меньше 1 грамма"
        if weight > 500_000:
            return False, (
                "Вес продукта должен быть не больше 500 000 г (500 кг)"
            )

        # Серверная валидация названия по регулярному выражению
        ok_name, name_error = validate_product_name(name)
        if not ok_name:
            return False, name_error

        display_name = normalize_product_name_display(name)

        is_valid, error_message = ProductService.validate_product_name_weight(
            user_id, display_name, weight, exclude_product_id=product_id
        )
        if not is_valid:
            return False, error_message

        product = (
            Product.query.join(Meal)
            .join(Day)
            .join(MealPlan)
            .filter(Product.id == product_id, MealPlan.user_id == user_id)
            .first()
        )

        if product:
            product.name = display_name
            product.weight = weight
            db.session.commit()
            return True, ""
        return False, "Продукт не найден или доступ запрещён"

    @staticmethod
    def delete_product(product_id: int, user_id: int) -> bool:
        """Удаляет продукт"""
        from raskladka import db

        product = (
            Product.query.join(Meal)
            .join(Day)
            .join(MealPlan)
            .filter(
                Product.id == product_id,
                MealPlan.user_id == user_id,
            )
            .first()
        )

        if product:
            db.session.delete(product)
            db.session.commit()
            return True
        return False


class BackupService:
    """Сервис для экспорта/импорта раскладок пользователя в/из JSON"""

    # ----- helpers -----
    @staticmethod
    def _parse_meal_plans_data(data: Dict[str, Any]) -> tuple[bool, list, str]:
        if not isinstance(data, dict):
            return False, [], "Некорректный формат бэкапа: ожидался объект"
        meal_plans_data = data.get("meal_plans", [])
        if not isinstance(meal_plans_data, list):
            return (
                False,
                [],
                "Некорректный формат бэкапа: отсутствует список 'meal_plans'",
            )
        return True, meal_plans_data, ""

    @staticmethod
    def _parse_created_at(created_at_str: Any) -> Optional[datetime]:
        if isinstance(created_at_str, str) and created_at_str:
            ts = created_at_str.rstrip("Z")
            try:
                return datetime.fromisoformat(ts)
            except Exception:  # noqa: BLE001
                return None
        return None

    @staticmethod
    def _iter_product_entries(meal_plans_data: list):
        for plan in meal_plans_data:
            days_data = plan.get("days", [])
            if not isinstance(days_data, list):
                continue
            for day in days_data:
                meals_data = day.get("meals", [])
                if not isinstance(meals_data, list):
                    continue
                for meal in meals_data:
                    products_data = meal.get("products", [])
                    if not isinstance(products_data, list):
                        continue
                    yield from BackupService._iter_products(products_data)

    @staticmethod
    def _iter_products(products_data: list):
        for product in products_data:
            raw_name = product.get("name", "")
            try:
                weight = int(product.get("weight", 0))
            except Exception:  # noqa: BLE001
                weight = 0
            if not raw_name or weight <= 0:
                continue
            key = canonical_product_key(str(raw_name))
            display_name = normalize_product_name_display(str(raw_name))
            yield key, display_name, weight

    @staticmethod
    def _collect_import_product_weights(
        meal_plans_data: list,
    ) -> tuple[Dict[str, set[int]], Dict[str, str]]:
        weights_by_key: Dict[str, set[int]] = {}
        display_by_key: Dict[str, str] = {}

        for key, display_name, weight in BackupService._iter_product_entries(
            meal_plans_data
        ):
            if key not in weights_by_key:
                weights_by_key[key] = set()
                display_by_key[key] = display_name
            weights_by_key[key].add(weight)

        return weights_by_key, display_by_key

    @staticmethod
    def _find_weight_conflicts_in_file(
        weights_by_key: Dict[str, set[int]],
        display_by_key: Dict[str, str],
    ) -> list[str]:
        conflicts: list[str] = []
        for key, weights in weights_by_key.items():
            if len(weights) > 1:
                sorted_weights = sorted(list(weights))
                name = display_by_key.get(key, "Продукт")
                conflicts.append(
                    "Продукт '"
                    + name
                    + "' имеет разные веса в файле: "
                    + ", ".join(str(w) + "г" for w in sorted_weights)
                )
        return conflicts

    @staticmethod
    def _build_existing_weight_by_key(user_id: int) -> Dict[str, int]:
        query = (
            Product.query.join(Meal)
            .join(Day)
            .join(MealPlan)
            .filter(MealPlan.user_id == user_id)
        )
        existing_products = query.all()
        existing_weight_by_key: Dict[str, int] = {}
        for product in existing_products:
            key = canonical_product_key(product.name)
            if key not in existing_weight_by_key:
                existing_weight_by_key[key] = product.weight
        return existing_weight_by_key

    @staticmethod
    def _find_conflicts_with_existing(
        weights_by_key: Dict[str, set[int]],
        display_by_key: Dict[str, str],
        existing_weight_by_key: Dict[str, int],
    ) -> list[str]:
        conflicts: list[str] = []
        for key, weights in weights_by_key.items():
            if key in existing_weight_by_key and len(weights) == 1:
                imported_weight = next(iter(weights))
                existing_weight = existing_weight_by_key[key]
                if imported_weight != existing_weight:
                    name = display_by_key.get(key, "Продукт")
                    conflicts.append(
                        "Продукт '"
                        + name
                        + "' имеет вес "
                        + str(existing_weight)
                        + "г в ваших раскладках, а в файле — "
                        + str(imported_weight)
                        + "г"
                    )
        return conflicts

    @staticmethod
    def _validate_before_import(
        user_id: int, meal_plans_data: list, replace: bool
    ) -> tuple[bool, str]:
        weights_by_key, display_by_key = (
            BackupService._collect_import_product_weights(meal_plans_data)
        )

        conflicts: list[str] = BackupService._find_weight_conflicts_in_file(
            weights_by_key, display_by_key
        )

        if not replace:
            existing_weight_by_key = (
                BackupService._build_existing_weight_by_key(user_id)
            )
            conflicts.extend(
                BackupService._find_conflicts_with_existing(
                    weights_by_key, display_by_key, existing_weight_by_key
                )
            )

        if conflicts:
            shown = conflicts[:5]
            more_count = max(0, len(conflicts) - 5)
            message = (
                "Импорт отменен. Обнаружены противоречия весов продуктов:\n- "
                + "\n- ".join(shown)
            )
            if more_count:
                message += f"\n… и еще {more_count} конфликт(а/ов)"
            return False, message

        return True, ""

    @staticmethod
    def _clear_user_plans(user_id: int) -> None:
        from raskladka import db

        existing_plans = MealPlan.query.filter_by(user_id=user_id).all()
        for plan in existing_plans:
            db.session.delete(plan)
        db.session.flush()

    @staticmethod
    def _import_products(meal: Meal, products_data: Any) -> None:
        from raskladka import db

        if not isinstance(products_data, list):
            products_data = []

        for product_data in products_data:
            raw_name = product_data.get("name", "")
            try:
                weight = int(product_data.get("weight", 0))
            except Exception:  # noqa: BLE001
                weight = 0
            if not raw_name or weight <= 0:
                continue

            display_name = normalize_product_name_display(str(raw_name))
            product = Product(meal=meal, name=display_name, weight=weight)
            db.session.add(product)

    @staticmethod
    def _import_meals(day: Day, meals_data: Any) -> None:
        from raskladka import db

        if not isinstance(meals_data, list):
            meals_data = []

        for meal_data in meals_data:
            meal_type = str(meal_data.get("meal_type", "Прием пищи"))[:50]
            meal = Meal(day=day, meal_type=meal_type)
            db.session.add(meal)
            BackupService._import_products(meal, meal_data.get("products", []))

    @staticmethod
    def _import_plan(user_id: int, plan_data: Dict[str, Any]) -> None:
        from raskladka import db

        name = str(plan_data.get("name", "Импортированная раскладка"))[:100]
        created_at_val = BackupService._parse_created_at(
            plan_data.get("created_at")
        )

        meal_plan = MealPlan(
            user_id=user_id,
            name=name,
            created_at=created_at_val or datetime.utcnow(),
        )
        db.session.add(meal_plan)

        days_data = plan_data.get("days", [])
        if not isinstance(days_data, list):
            days_data = []

        for day_data in sorted(
            days_data, key=lambda d: int(d.get("day_number", 0))
        ):
            try:
                day_number = int(day_data.get("day_number", 0))
            except Exception:  # noqa: BLE001
                day_number = 0
            if day_number <= 0:
                continue

            day = Day(meal_plan=meal_plan, day_number=day_number)
            db.session.add(day)
            BackupService._import_meals(day, day_data.get("meals", []))

    @staticmethod
    def export_user_data(user_id: int) -> Dict[str, Any]:
        """Собирает все раскладки пользователя в словарь для JSON-бэкапа."""
        data: Dict[str, Any] = {
            "version": 1,
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "meal_plans": [],
        }

        plans: List[MealPlan] = MealPlan.query.filter_by(user_id=user_id).all()
        for plan in plans:
            plan_dict: Dict[str, Any] = {
                "name": plan.name,
                "created_at": plan.created_at.isoformat() + "Z"
                if isinstance(plan.created_at, datetime)
                else None,
                "days": [],
            }

            # Гарантируем детерминированный порядок дней
            for day in sorted(plan.days, key=lambda d: d.day_number):
                day_dict: Dict[str, Any] = {
                    "day_number": day.day_number,
                    "meals": [],
                }
                for meal in day.meals:
                    meal_dict: Dict[str, Any] = {
                        "meal_type": meal.meal_type,
                        "products": [],
                    }
                    for product in meal.products:
                        meal_dict["products"].append(
                            {
                                "name": product.name,
                                "weight": product.weight,
                            }
                        )
                    day_dict["meals"].append(meal_dict)
                plan_dict["days"].append(day_dict)

            data["meal_plans"].append(plan_dict)

        return data

    @staticmethod
    def import_user_data(
        user_id: int, data: Dict[str, Any], replace: bool = True
    ) -> tuple[bool, str]:
        """Импортирует раскладки пользователя из словаря JSON.

        Args:
            user_id: ID текущего пользователя
            data: распарсенный JSON
            replace: если True — удаляет текущие раскладки пользователя
                и заменяет из бэкапа
        """
        from raskladka import db

        try:
            ok, meal_plans_data, error = BackupService._parse_meal_plans_data(
                data
            )
            if not ok:
                return False, error

            valid, validation_error = BackupService._validate_before_import(
                user_id, meal_plans_data, replace
            )
            if not valid:
                return False, validation_error

            if replace:
                BackupService._clear_user_plans(user_id)

            for plan_data in meal_plans_data:
                BackupService._import_plan(user_id, plan_data)

            db.session.commit()
            return True, "Импорт выполнен успешно"

        except Exception as e:  # noqa: BLE001
            db.session.rollback()
            return False, (
                "Ошибка импорта: " + str(e)
            )


class SettingsService:
    """Сервис для сохранения пользовательских настроек расчета по плану."""

    @staticmethod
    def get_user_plan_settings(user_id: int, plan_id: int) -> dict:
        """Возвращает сохраненные настройки trip_days и people_count.

        Если настроек нет — возвращает пустой словарь.
        """
        settings = UserPlanSettings.query.filter_by(
            user_id=user_id, plan_id=plan_id
        ).first()
        if not settings:
            return {}
        return {
            "trip_days": settings.trip_days,
            "people_count": settings.people_count,
            "params_locked": bool(getattr(settings, "params_locked", False)),
            "updated_at": (
                settings.updated_at.isoformat()
                if settings.updated_at
                else None
            ),
        }

    @staticmethod
    def upsert_user_plan_settings(
        user_id: int,
        plan_id: int,
        trip_days: Optional[int] = None,
        people_count: Optional[int] = None,
        params_locked: Optional[bool] = None,
    ) -> None:
        from raskladka import db

        settings = UserPlanSettings.query.filter_by(
            user_id=user_id, plan_id=plan_id
        ).first()
        if settings:
            if trip_days is not None:
                settings.trip_days = trip_days
            if people_count is not None:
                settings.people_count = people_count
            if params_locked is not None and hasattr(
                settings, "params_locked"
            ):
                settings.params_locked = bool(params_locked)
        else:
            # Если настроек нет, создаем с разумными значениями
            # Берем дефолты, если параметры не переданы
            default_trip_days = trip_days
            default_people_count = people_count
            if default_trip_days is None or default_people_count is None:
                # Попробуем получить план и взять длину дней;
                # people_count = 1 по умолчанию
                plan = (
                    MealPlan.query.filter_by(
                        id=plan_id, user_id=user_id
                    ).first()
                )
                if default_trip_days is None:
                    default_trip_days = (
                        len(plan.days) if plan and plan.days else 1
                    )
                if default_people_count is None:
                    default_people_count = 1

            settings = UserPlanSettings(
                user_id=user_id,
                plan_id=plan_id,
                trip_days=int(default_trip_days),
                people_count=int(default_people_count),
                params_locked=(bool(params_locked)
                               if params_locked is not None else False),
            )
            db.session.add(settings)
        db.session.commit()
