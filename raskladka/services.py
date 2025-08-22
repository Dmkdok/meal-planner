# raskladka/services.py
from typing import List, Dict, Any
from raskladka.models import MealPlan, Day, Meal, Product


class CalculationService:
    """Сервис для расчета продуктов на основе раскладки"""

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

        # Собираем все продукты из раскладки
        products_map = {}  # product_name -> {weight, occurrences, meal_types}

        for day in meal_plan.days:
            for meal in day.meals:
                for product in meal.products:
                    product_name = product.name
                    product_weight = product.weight

                    if product_name in products_map:
                        products_map[product_name]["weight"] += product_weight
                        products_map[product_name]["occurrences"] += 1
                        if (
                            meal.meal_type
                            not in products_map[product_name]["meal_types"]
                        ):
                            products_map[product_name]["meal_types"].append(
                                meal.meal_type
                            )
                    else:
                        products_map[product_name] = {
                            "weight": product_weight,
                            "occurrences": 1,
                            "meal_types": [meal.meal_type],
                        }

        if not products_map:
            return {"error": "В раскладке нет продуктов", "success": False}

        # Рассчитываем количество повторений раскладки
        layout_days_count = len(meal_plan.days)
        layout_repetitions = (
            trip_days + layout_days_count - 1
        ) // layout_days_count  # Округление вверх
        actual_days_used = layout_repetitions * layout_days_count

        # Генерируем результаты
        results = []
        for product_name, product_data in products_map.items():
            total_weight = product_data["weight"] * layout_repetitions * people_count
            total_occurrences = product_data["occurrences"] * layout_repetitions
            weight_per_meal = product_data["weight"] / product_data["occurrences"]

            results.append(
                {
                    "name": product_name,
                    "weight": total_weight,
                    "occurrences": total_occurrences,
                    "weight_per_meal": weight_per_meal,
                    "meal_types": product_data["meal_types"],
                    "unit": "г",
                }
            )

        # Сортируем результаты по весу (по убыванию)
        results.sort(key=lambda x: x["weight"], reverse=True)

        # Собираем информацию о рационах по дням
        meal_types_by_day = []
        product_meal_usage = {}  # product_name -> {day_index: count}

        for day_index, day in enumerate(meal_plan.days):
            day_meal_types = []
            for meal in day.meals:
                if meal.products:
                    day_meal_types.append(meal.meal_type)

                for product in meal.products:
                    product_name = product.name
                    if product_name not in product_meal_usage:
                        product_meal_usage[product_name] = {}
                    product_meal_usage[product_name][day_index] = (
                        product_meal_usage[product_name].get(day_index, 0) + 1
                    )

            meal_types_by_day.append(day_meal_types)

        # Рассчитываем общий вес
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
    def create_default_plan(user_id: int, name: str = "Current Plan") -> MealPlan:
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
        return MealPlan.query.filter_by(id=plan_id, user_id=user_id).first()

    @staticmethod
    def delete_plan(plan_id: int, user_id: int) -> bool:
        """Удаляет план питания"""
        from raskladka import db

        meal_plan = MealPlan.query.filter_by(id=plan_id, user_id=user_id).first()
        if meal_plan:
            db.session.delete(meal_plan)
            db.session.commit()
            return True
        return False

    @staticmethod
    def update_plan_name(plan_id: int, user_id: int, new_name: str) -> bool:
        """Обновляет название плана питания"""
        from raskladka import db

        meal_plan = MealPlan.query.filter_by(id=plan_id, user_id=user_id).first()
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

        meal_plan = MealPlan.query.filter_by(id=plan_id, user_id=user_id).first()
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
    def add_meal(plan_id: int, user_id: int, day_number: int, meal_type: str) -> bool:
        """Добавляет новый прием пищи"""
        from raskladka import db

        meal_plan = MealPlan.query.filter_by(id=plan_id, user_id=user_id).first()
        if meal_plan:
            day = Day.query.filter_by(
                meal_plan_id=plan_id, day_number=day_number
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
            .filter(Meal.id == meal_id, MealPlan.user_id == user_id)
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
    def add_product(meal_id: int, user_id: int, name: str, weight: int) -> bool:
        """Добавляет новый продукт"""
        from raskladka import db

        meal = (
            Meal.query.join(Day)
            .join(MealPlan)
            .filter(Meal.id == meal_id, MealPlan.user_id == user_id)
            .first()
        )

        if meal:
            new_product = Product(meal=meal, name=name, weight=weight)
            db.session.add(new_product)
            db.session.commit()
            return True
        return False

    @staticmethod
    def update_product(product_id: int, user_id: int, name: str, weight: int) -> bool:
        """Обновляет продукт"""
        from raskladka import db

        product = (
            Product.query.join(Meal)
            .join(Day)
            .join(MealPlan)
            .filter(Product.id == product_id, MealPlan.user_id == user_id)
            .first()
        )

        if product:
            product.name = name
            product.weight = weight
            db.session.commit()
            return True
        return False

    @staticmethod
    def delete_product(product_id: int, user_id: int) -> bool:
        """Удаляет продукт"""
        from raskladka import db

        product = (
            Product.query.join(Meal)
            .join(Day)
            .join(MealPlan)
            .filter(Product.id == product_id, MealPlan.user_id == user_id)
            .first()
        )

        if product:
            db.session.delete(product)
            db.session.commit()
            return True
        return False
