class Prompt:
    def __init__(self, objeto) -> None:
        self.name = objeto.get('name')
        self.description = objeto.get('description')
        self.objeto = objeto

    def audio_tts_ou_uri(self) -> str:
        self.tts = None
        self.media_uri = None
        for prompt in self.objeto['resources']:
            if prompt.get('language') == 'pt-br':
                self.tts = prompt.get('ttsString')
                self.media_uri = prompt.get('mediaUri')
                break
        return {'prompt-url':self.media_uri} if self.media_uri != None else {'prompt-tts':self.tts}