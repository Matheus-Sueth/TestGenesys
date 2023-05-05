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


def AddItem(lista: list, item: object) -> list:
    lista.append(item)
    return lista


def AudioPlaybackOptions(*args):
    pass


def ToAudio(*args):
    pass