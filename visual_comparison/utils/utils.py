import subprocess


__all__ = ["validate_number_str", "do_cmd"]


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


def do_cmd(s_cmd):
    child = subprocess.Popen(s_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    res = child.communicate()  # stdout stderr include '\n'
    ret = child.returncode

    return ret, res[0], res[1]
