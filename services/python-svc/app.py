def add(a: int, b: int) -> int:
    return a + b


def slugify(text: str) -> str:
    return "-".join(text.lower().split())
