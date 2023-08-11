import random
import datetime
import types
import json
from .Genesys import Genesys


def ToAudioBlank(mili_segundos) -> str:
    return f'Aguardar {mili_segundos} Milissegundos'


def GetCurrentDateTimeUtc() -> datetime:
    return datetime.datetime.today()


def Length(text: str) -> int:
    return len(text)-2 if text[0] == '"' and text[-1] == '"' else len(text)


def Count(arg: list) -> int:
    return len(arg) if not arg is None else 0


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


def ToAudio(arg):
    return arg


def Append(*args):
    return ' '.join([str(arg) for arg in args if arg != None])


def ToAudioTTS(arg):
    return arg


def AudioPlaybackOptions(*args):
    return args[0]


def ToAudioNumber(arg):
    return str(arg)


def If(condicao, verdadeiro, falso):
    return verdadeiro if condicao else falso


def GetAt(lista: list, indice: int):
    return lista[indice]


def FindUserPrompt(name_prompt: str):
    return name_prompt


def IsNotSetOrEmpty(arg):
    return True if arg == None or arg == '' else False


def MakeList(*args):
    return [arg for arg in args]


def Find(lista: list, indice: int):
    try:
        return lista.index(indice)
    except:
        return None


def ToInt(arg) -> int:
    return int(arg)


def Substring(variavel, indice_inicial, quantidade):
    return variavel[indice_inicial:indice_inicial+quantidade]


def Hour(date_time: datetime.datetime):
    return date_time.hour


def Minute(date_time: datetime.datetime):
    return date_time.minute


def Second(date_time: datetime.datetime):
    return date_time.second


def DateTimeDiff(date_time1: datetime.datetime , date_time2: datetime.datetime):
    return (date_time1 - date_time2).total_seconds()


def FindString(string_to_search: str, text_to_find: str) -> int:
    return string_to_search.find(text_to_find)


def Right(texto: str, quantidade: int):
    return texto[-quantidade:]


def Left(texto: str, quantidade: int):
    return texto[:quantidade]


def Contains(string_to_search: str, text_to_find: str) -> bool:
    return text_to_find in string_to_search


def JsonParse(value_to_parse: str) -> dict:
    return json.loads(value_to_parse)


def IsJsonArray(value_to_check: any) -> bool:
    return True if isinstance(value_to_check, list) and len(value_to_check) > 0 else False


def Year(date_time: datetime.datetime) -> int:
    return date_time.year


def Lower(arg: str):
    return arg.lower()


def GetJsonObjectProperty(objeto: dict, chave):
    return objeto[chave]


def MakeDateTime(year: int, month: int, day: int, hour: int = 12, minute: int = 0, second: int = 0) -> datetime.datetime:
    if year < 1800 or year > 2200:
        raise Exception(f'campo year deve estar entre 1800 e 2200, valor passado: {year}')
    
    return datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)


all_functions = [valor for valor in globals().values() if isinstance(valor, types.FunctionType)]
my_functions = [funcao.__name__ for funcao in all_functions]