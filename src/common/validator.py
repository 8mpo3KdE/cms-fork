import re

schema = {
    "name": {
        "type": "str",
        "min": 1,
        "max": 48,
        "regex": "[a-zA-Z0-9_][a-zA-Z0-9_\.\-]*"
    },
    "k8s-name": {
        "type": "str",
        "min": 1,
        "max": 48,
        "regex": "[a-z][a-z0-9\-]*"
    },
    "size-volume": {
        "type": "int",
        "min": 1,
        "max": 1000000
    },
    "size-control": {
        "type": "int",
        "min": 1,
        "max": 5
    },
    "domain": {
        "type": "str",
        "min": 1,
        "max": 253,
        "regex": "[a-z][a-z\.\-]*[a-z]"
    },
    "dns-label": {
        "type": "str",
        "min": 1,
        "max": 63,
        "regex": "[a-z][a-z\-]*[a-z]"
    },
    "cron-expr": {
        "type": "cron-expr",
        "min": 9,
        "max": 256,
        "regex": "[a-zA-Z0-9\,\ \-\*\/]*"
    }
}


def is_valid(var, name):
    if name not in schema.keys():
        return False
    s = schema[name]
    if s["type"] == "int":
        if type(var) != int:
            return False
        if (var < s["min"]) or (var > s["max"]):
            return False
    elif s["type"] == "str":
        if type(var) != str:
            return False
        if (len(var) < s["min"]) or (len(var) > s["max"]):
            return False
        if re.fullmatch(s["regex"], var) is None:
            return False
    elif s["type"] == "cron-expr":
        if type(var) != str:
            return False
        if (len(var) < s["min"]) or (len(var) > s["max"]):
            return False
        if re.fullmatch(s["regex"], var) is None:
            return False
        if len(var.split(" ")) != 5:
            return False
    return True


def validate(req, v):
    for k in v.keys():
        if not is_valid(req[k], v[k]):
            return f"Argument {k} is invalid!"

