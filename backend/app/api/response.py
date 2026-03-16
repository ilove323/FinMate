from typing import Any


def success(data: Any = None, message: str = "ok") -> dict:
    return {"code": 200, "data": data, "message": message}


def error(code: int = 400, message: str = "error") -> dict:
    return {"code": code, "data": None, "message": message}
