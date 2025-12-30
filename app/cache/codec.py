import orjson


def encode(value: dict) -> bytes:
    """Сериализация dict -> bytes"""
    return orjson.dumps(value)


def decode(data: bytes | None):
    """Десериализация bytes -> dict | None"""
    if not data:
        return None
    return orjson.loads(data)
