class Task:
    def definir_dados(self, **kwargs) -> None:
        for chave, valor in kwargs.items():
            setattr(self, chave, valor)
    
    def clear_dados(self) -> None:
       for chave in list(vars(self).keys()):
            delattr(self, chave) 

class Flow:
    IsTest = ''
    StartDateTimeUtc = ''
    Version = ''

    def definir_dados(self, **kwargs) -> None:
        for chave, valor in kwargs.items():
            setattr(self, chave, valor)

class Call:
    Ani = 'tel:+5511969858000'
    CalledAddress = '4004'
    CalledAddressOriginal = '4004'
    ConversationId = '1234-5678-9012-3456'
    ExternalTag = ''
    Language = ''
    RemoteName = ''
    UUIData = ''

class System:
    def __init__(self) -> None:
        self.Conversation = ''
        self.Currencies = ''
        self.DateTime = ''
        self.Languages = ''
        self.MaxDateTime = ''
        self.MaxDuration = ''
        self.MaxInt = ''
        self.MinDateTime = ''
        self.MinDuration = ''
        self.MinInt = ''
        self.Regions = ''
        self.Survey = ''

class Interaction:
    Id = ''

class Menu:
    LastCollectionNoInput = ''
    LastCollectionNoMatch = ''

class PromptSystem:
    processing = 'Processando dados'

class Attributte:
    def definir_dados(self, **kwargs) -> None:
        for chave, valor in kwargs.items():
            setattr(self, chave, valor)
