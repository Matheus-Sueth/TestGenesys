import random


def Length(text: str) -> int:
    return len(text)


def Count(*args: list) -> int:
    return len(args)


def randomInt(limit: int) -> int:
    if limit < 0:
        return random.randint(limit, 0)
    else:
        return random.randint(0,limit)
    
def ToString(value) -> str:
    return str(value)