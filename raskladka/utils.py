# raskladka/utils.py
from typing import Union
import re


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
    Приводит название продукта к виду,
    где заглавной является только первая буква строки.
    Убирает лишние пробелы (сворачивает кратные в один).
    Пример: "  пШено  крупа" -> "Пшено крупа"
    """
    if not isinstance(name, str):
        return name
    # Убираем лишние пробелы по краям и внутри сворачиваем кратные пробелы
    compact = " ".join(name.strip().split())
    if not compact:
        return ""
    lowered = compact.lower()
    return lowered[0].upper() + lowered[1:]


def canonical_product_key(name: str) -> str:
    """
    Канонический ключ для сравнения/объединения продуктов: case-insensitive
    и без лишних пробелов. Использует .casefold() для надёжного сравнения
    с учетом локалей. Пример: " пШено  " -> "пшено"
    """
    if not isinstance(name, str):
        return str(name)
    return " ".join(name.strip().split()).casefold()


def canonical_username(username: str) -> str:
    """
    Канонический вид имени пользователя: обрезает пробелы по краям
    и приводит к нижнему регистру (casefold) для надежного сравнения.
    Примеры:
      " Dmkdok " -> "dmkdok"
      "dmkdok"  -> "dmkdok"
    """
    if not isinstance(username, str):
        return str(username)
    return username.strip().casefold()


# Разрешенные символы логина: только латинские буквы, цифры и . _ -
_USERNAME_REGEX = re.compile(r"^[A-Za-z0-9._-]+$")


def validate_username(username: str) -> tuple[bool, str]:
    """
    Валидирует имя пользователя (логин):
    - только латинские буквы (A-Z, a-z), цифры (0-9)
    - разрешенные символы: точка (.), подчеркивание (_), дефис (-)
    - длина от 3 до 30 символов
    """
    if not isinstance(username, str):
        return False, "Некорректное имя пользователя"
    trimmed = username.strip()
    if not trimmed:
        return False, "Введите имя пользователя"
    if len(trimmed) < 3 or len(trimmed) > 30:
        return False, "Имя пользователя должно быть от 3 до 30 символов"
    if not _USERNAME_REGEX.match(trimmed):
        return (
            False,
            "Имя пользователя может содержать только латинские буквы, цифры и"
            " символы . _ -",
        )
    return True, ""


# Разрешаем все буквы и цифры (Unicode), пробелы и основные символы
# - _ . , ( ) / + % & : ; ' " №
_PRODUCT_NAME_REGEX = re.compile(r"^[\w\s\-\.,()/+%&:;'\"№_]+$", re.UNICODE)


def validate_product_name(name: str) -> tuple[bool, str]:
    """
    Валидирует название продукта по регулярному выражению:
    - допускаются все буквы и цифры (Unicode)
    - пробелы
    - основные символы: - _ . , ( ) / + % & : ; ' " №
    """
    if not isinstance(name, str):
        return False, "Некорректное название продукта"
    trimmed = name.strip()
    if not trimmed:
        return False, "Введите название продукта"
    if len(trimmed) > 100:
        return False, "Название продукта не должно превышать 100 символов"
    if not _PRODUCT_NAME_REGEX.match(trimmed):
        return False, "Название продукта содержит недопустимые символы"
    return True, ""