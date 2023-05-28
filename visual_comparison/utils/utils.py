

__all__ = ["validate_number_str"]


def validate_number_str(string, desired_type):
    if not (desired_type is int or desired_type is float):
        raise ValueError("desired_type should be either int or float")

    if string is None or string == "":
        return False, None

    try:
        value = desired_type(string)
    except ValueError:
        return False, None

    return True, value
