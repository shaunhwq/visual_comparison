

__all__ = ["validate_int_str", "validate_float_str"]


def validate_int_str(integer_string):
    if integer_string is None or integer_string == "":
        return False, None

    try:
        value = int(integer_string)
    except ValueError:
        return False, None

    return True, value


def validate_float_str(float_string):
    if float_string is None or float_string == "":
        return False, None

    try:
        value = float(float_string)
    except ValueError:
        return False, None
    return True, value
