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
