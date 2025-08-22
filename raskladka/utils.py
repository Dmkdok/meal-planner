# raskladka/utils.py
from typing import Union


def validate_positive_integer(
    value: Union[str, int], field_name: str = "Значение"
) -> tuple[bool, str]:
    """
    Валидирует, что значение является положительным целым числом

    Args:
        value: Значение для валидации
        field_name: Название поля для сообщения об ошибке

    Returns:
        Кортеж (is_valid, error_message)
    """
    try:
        int_value = int(value)
        if int_value <= 0:
            return False, f"{field_name} должно быть положительным числом"
        return True, ""
    except (ValueError, TypeError):
        return False, f"{field_name} должно быть числом"


def normalize_product_name_display(name: str) -> str:
    """
    Приводит название продукта к виду с большой первой буквы в каждом слове,
    аккуратно обрабатывая лишние пробелы и дефисы.
    Пример: "  пШено  крупа" -> "Пшено Крупа"
    """
    if not isinstance(name, str):
        return name
    # Убираем лишние пробелы по краям и внутри сворачиваем кратные пробелы
    compact = " ".join(name.strip().split())

    # Для дефисных составных слов применяем capital case по частям
    def title_keep_hyphen(token: str) -> str:
        if "-" in token:
            return "-".join(part.capitalize() for part in token.split("-"))
        return token.capitalize()

    return " ".join(title_keep_hyphen(tok) for tok in compact.split(" "))


def canonical_product_key(name: str) -> str:
    """
    Канонический ключ для сравнения/объединения продуктов: case-insensitive
    и без лишних пробелов. Использует .casefold() для надёжного сравнения
    с учетом локалей. Пример: " пШено  " -> "пшено"
    """
    if not isinstance(name, str):
        return str(name)
    return " ".join(name.strip().split()).casefold()