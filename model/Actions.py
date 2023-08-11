from fastapi import WebSocket
from functools import reduce
from .Genesys import Genesys
from .Message import Message


class transferToFlow(Message):
    def __init__(self, chave, valor, ws) -> None:
        super().__init__(ws)
        self.chave = chave
        self.flow_name = valor['targetFlow']['name']
    
    async def enviar_mensagem(self) -> None:
        await self.web_socket.send_json({self.chave: f"Transferindo para o fluxo: {self.flow_name}"})


class playAudio(Message):
    def __init__(self, chave, valor, api: Genesys, ws, fluxo) -> None:
        super().__init__(ws)
        self.chave = chave
        self.objeto = valor
        self.api_genesys = api
        self.fluxo = fluxo
    
    async def enviar_mensagem(self) -> None:
        if self.objeto['audio'].get('prompt'):
            name_prompt: str = self.objeto['audio']['prompt']
            prompt = await self.ler_prompt(name_prompt)
        elif self.objeto['audio'].get('tts'):
            prompt = {'prompt-tts':self.objeto['audio']['tts']}
        else:
            valor_prompt = await self.fluxo.trocar_variavel_pelo_valor(self.objeto['audio']['exp'])
            prompt = await self.ler_prompt(valor_prompt)
        await self.web_socket.send_json(prompt)

    async def ler_prompt(self, prompt: str) -> dict:
        inicio_prompt = prompt.find('Prompt.')
        name_prompt =  prompt[inicio_prompt+7:]
        try:
            model_prompt = self.api_genesys.procurar_prompt(name_prompt)
            prompt = model_prompt.audio_tts_ou_uri()
        except Exception as erro:
            prompt = {'prompt-name':prompt}
            #print(f'Erro na função ler_prompt: {erro}\nPrompt: {prompt}\nName Prompt: {prompt}')
        finally:
            return prompt
        

class setParticipantData(Message):
    def __init__(self, ws, chave, valor, fluxo) -> None:
        super().__init__(ws)
        self.chave = chave
        self.valor = valor
        self.fluxo = fluxo

    async def enviar_mensagem(self) -> None:
        for atributo in self.valor['attributes']:
            atributo_name = atributo['attribute']['name']['lit'] if atributo['attribute']['name'].get('lit') else atributo['attribute']['name']['exp']
            if atributo['attribute']['value'].get('exp'):
                atributo_value = atributo['attribute']['value']['exp']
                atributo_value = await self.fluxo.trocar_variavel_pelo_valor(atributo_value)
            else:
                atributo_value = atributo['attribute']['value']['lit']
            if atributo_value != None:
                self.fluxo.attribute.definir_dados(**{atributo_name: str(atributo_value)})
                await self.web_socket.send_json({self.chave: f"{atributo_name} = {atributo_value}"})


class getParticipantData(Message):
    def __init__(self, ws: WebSocket, chave, valor, fluxo) -> None:
        super().__init__(ws)
        self.chave = chave
        self.valor = valor
        self.fluxo = fluxo

    async def enviar_mensagem(self) -> None:
        for atributo in self.valor['attributes']:
            atributo_name = atributo['attribute']['name']['lit'] if atributo['attribute']['name'].get('lit') else atributo['attribute']['name']['exp']
            atributo_variavel = atributo['attribute']['variable']
            try:
                atributo_value = getattr(self.fluxo.attribute, atributo_name)
            except:
                atributo_value = None
                self.fluxo.attribute.definir_dados(**{atributo_name: atributo_value})
            await self.fluxo.definir_variavel_global_ou_local(atributo_variavel, atributo_value)
            await self.web_socket.send_json({self.chave: f'{atributo_variavel} = {atributo_value}'})


class decision(Message):
    def __init__(self, ws: WebSocket, chave, valor, fluxo, objeto_tarefa) -> None:
        super().__init__(ws)
        self.chave = chave
        self.valor = valor
        self.fluxo = fluxo
        self.objeto_tarefa = objeto_tarefa

    async def enviar_mensagem(self) -> None:
        condition = self.valor['condition']['exp']  
        condition = await self.fluxo.trocar_variavel_pelo_valor(condition)
        name = self.valor['name']
        saida = self.valor.get('outputs')
        if saida is None:
            raise Exception(f'erro decision {name}: {self.chave} = {self.valor}, {self.objeto_tarefa}')
        match condition:
            case True:
                chave = 'yes'
            case False:
                chave = 'no'
            case _:
                await self.web_socket.send_json({self.chave: f'{condition} é verdadeira? yes/no'})
                chave = await self.web_socket.receive_text()
                await self.web_socket.send_json({"collectInput": f'Entrada: {chave}'})

        try:
            await self.fluxo.doc_genesys(saida[chave]['actions'])
        except:
            pass


class disconnect(Message):
    def __init__(self, ws: WebSocket, chave, valor, fluxo) -> None:
        super().__init__(ws)
        self.chave = chave
        self.valor = valor
        self.fluxo = fluxo

    async def enviar_mensagem(self) -> None:
        self.fluxo.finaliza_loop = True
        await self.web_socket.send_json({"playAudio": "Desconectando URA"})


class jumpToTask(Message):
    def __init__(self, ws: WebSocket, chave, valor, fluxo) -> None:
        super().__init__(ws)
        self.chave = chave
        self.valor = valor
        self.fluxo = fluxo

    async def enviar_mensagem(self) -> None:
        name_task = self.valor['name']
        self.fluxo.proxima_task = ref_task = self.valor['targetTaskRef']
        await self.web_socket.send_json({self.chave: f'{name_task} = {ref_task}'})


class updateData(Message):
    def __init__(self, ws: WebSocket, chave, valor, fluxo) -> None:
        super().__init__(ws)
        self.chave = chave
        self.valor = valor
        self.fluxo = fluxo

    async def enviar_mensagem(self):
        name_data = self.valor['name']
        for var in self.valor['statements']:
            for chave, valor in var.items():
                if chave == 'prompt':
                    if valor['value'].get('lit') != None:
                        valor_var = valor['value']['lit']['name']  
                    else:
                        valor_var = await self.fluxo.trocar_variavel_pelo_valor(valor['value']['exp'])
                elif valor['value'].get('lit') != None:
                    valor_var = valor["value"]["lit"]
                    if type(valor_var) == list:
                        for var in  valor_var:
                            valor_var = await self.fluxo.trocar_variavel_pelo_valor(str(var['exp']))
                    if type(valor_var) == str:
                        valor_var = await self.fluxo.trocar_variavel_pelo_valor(str(valor_var))
                else:
                    valor_var = await self.fluxo.trocar_variavel_pelo_valor(valor['value']['exp'])
                
                await self.fluxo.definir_variavel_global_ou_local(valor['variable'], valor_var)
                await self.web_socket.send_json({'updateData': f'{name_data} - {valor["variable"]}: {chave} = {valor_var}'})


class setWrapupCode(Message):
    def __init__(self, ws: WebSocket, chave, valor) -> None:
        super().__init__(ws)
        self.chave = chave
        self.valor = valor

    async def enviar_mensagem(self):
        wrapup_code = self.valor['wrapupCode']['lit']['name']
        await self.web_socket.send_json({self.chave: f'wrapup_code = {wrapup_code}'})


class switch(Message):
    def __init__(self, ws: WebSocket, chave, valor, fluxo) -> None:
        super().__init__(ws)
        self.chave = chave
        self.valor = valor
        self.fluxo = fluxo

    async def enviar_mensagem(self):
        for case in self.valor['evaluate']['firstTrue']['cases']:
            exp = case['case']['value']['exp']
            condition = await self.fluxo.trocar_variavel_pelo_valor(exp)
            match condition:
                case True:
                    await self.fluxo.doc_genesys(case['case']['actions'])
                    break
                case False:
                    continue
                case _:
                    await self.web_socket.send_json({self.chave: f'{condition} é verdadeira? yes/no'})
                    acessar_case = await self.web_socket.receive_text()
                    await self.web_socket.send_json({"collectInput": f'Entrada: {acessar_case}'})

                    if acessar_case == 'yes':
                        await self.fluxo.doc_genesys(case['case']['actions'])
                        break
        else:
            if self.valor['evaluate']['firstTrue'].get('default'):
                await self.fluxo.doc_genesys(self.valor['evaluate']['firstTrue']['default']['actions'])


class collectInput(Message):
    def __init__(self, ws: WebSocket, chave, valor, fluxo) -> None:
        super().__init__(ws)
        self.chave = chave
        self.valor = valor
        self.fluxo = fluxo

    async def enviar_mensagem(self):
        if 'AudioPlaybackOptions(Append(' in self.valor['inputAudio']['exp']:
            prompt = self.valor['inputAudio']
            dados = await self.fluxo.trocar_variavel_pelo_valor(prompt['exp'])
            lista_prompts = dados.split(' ')
            for audio in lista_prompts:
                valor = {"audio": {"exp": audio}}
                action = playAudio('prompt', valor, self.fluxo.api_genesys, self.web_socket, self.fluxo)
                await action.enviar_mensagem()
        else:
            valor = {"audio": self.valor['inputAudio']}
            action = playAudio('prompt', valor, self.fluxo.api_genesys, self.web_socket, self.fluxo)
            await action.enviar_mensagem()
        name_var = self.valor['inputData']['var']
        value_var = await self.web_socket.receive_text()
        await self.web_socket.send_json({self.chave: f'Entrada: {value_var}'})
        await self.fluxo.definir_variavel_global_ou_local(name_var, value_var)
        if value_var != "":
            await self.fluxo.doc_genesys(self.valor['outputs']['success']['actions'])
        else:
            await self.fluxo.doc_genesys(self.valor['outputs']['failure']['actions'])


class loop(Message):
    def __init__(self, ws: WebSocket, chave, valor, fluxo) -> None:
        super().__init__(ws)
        self.chave = chave
        self.valor = valor
        self.fluxo = fluxo

    async def enviar_mensagem(self):
        var_loop = self.valor['currentIndex']['var']
        count_loop = self.valor['loopCount']['lit'] if not self.valor['loopCount'].get('lit') is None else await self.fluxo.trocar_variavel_pelo_valor(self.valor['loopCount']['exp'])
        for index in range(count_loop):
            await self.fluxo.definir_variavel_global_ou_local(var_loop, index)
            await self.fluxo.doc_genesys(self.valor['outputs']['loop']['actions'])
            if self.fluxo.finaliza_loop or self.fluxo.proxima_task:
                self.fluxo.finaliza_loop = False
                break
            else:
                continue


class dataTableLookup(Message):
    def __init__(self, ws: WebSocket, chave, valor, api: Genesys, fluxo) -> None:
        super().__init__(ws)
        self.chave = chave
        self.valor = valor
        self.api = api
        self.fluxo = fluxo
    
    async def enviar_mensagem(self):
        lookup_value = self.valor['lookupValue']['lit'] if self.valor['lookupValue'].get('lit') else await self.fluxo.trocar_variavel_pelo_valor(self.valor['lookupValue']['exp'])

        name_data_table = list(self.valor['dataTable'].values())[0]
        try:
            row = self.api.procurar_row_data_table(self.api.procurar_data_table(name_data_table), lookup_value)
            output, saida = 'failureOutputs','notFound' if row.get('status') == 404 and row.get('message') == 'Not found' else 'foundOutputs','found'
            for column_name in self.valor['dataTable'][name_data_table][output].values():
                variavel_name = self.valor['dataTable'][name_data_table][output][column_name].get('var')
                await self.fluxo.definir_variavel_global_ou_local(variavel_name, row.get(column_name))
        except:
            saida = 'failure'
        finally:
            await self.fluxo.doc_genesys(self.valor['outputs'][saida]['actions'])


class callData(Message):
    def __init__(self, ws: WebSocket, chave, valor, api: Genesys, fluxo) -> None:
        super().__init__(ws)
        self.chave = chave
        self.valor = valor
        self.api = api
        self.fluxo = fluxo
    
    async def enviar_mensagem(self):
        if self.valor['processingPrompt'].get('noValue') is None:
            valor_prompt = self.valor['processingPrompt']['lit']['name'] if self.valor['processingPrompt'].get('lit') else self.valor['processingPrompt']['exp']
            action = playAudio('prompt', {'audio':{'prompt':valor_prompt}}, self.fluxo.api_genesys, self.web_socket, self.fluxo)
            await action.enviar_mensagem()

        if self.valor['timeout'].get('lit'):
            tempo_timeout = self.valor['timeout']['lit']['minutes'] * 60  
        else:
            tempo_timeout = await self.fluxo.trocar_variavel_pelo_valor(self.valor['timeout']['exp'])

        category = list(self.valor['category'].keys())[0]
        name_data_action = list(self.valor['category'][category]['dataAction'].keys())[0]
        body = {}
        for chave, valor in self.valor['category'][category]['dataAction'][name_data_action]['inputs'].items():
            if valor.get('noValue'):
                continue
            dado = valor['lit'] if not valor.get('lit') is None else await self.fluxo.trocar_variavel_pelo_valor(valor['exp'])
            body[chave] = str(dado)
        data_action = self.api.procurar_data_action(category, name_data_action)
        dados, saida = self.api.executar_data_action(data_action['id'], body, tempo_timeout)
        if saida == 'success':
            for chave, valor in self.valor['category'][category]['dataAction'][name_data_action]['successOutputs'].items():
                items = chave.split('.')
                retorno = self.get_valor_objeto(dados['finalResult'], items) if not dados.get('finalResult') is None else self.get_valor_objeto(dados['error'], items)
                if not valor.get('noValue') is None or retorno is None:
                    continue
                await self.fluxo.definir_variavel_global_ou_local(valor['var'], retorno)

        await self.fluxo.doc_genesys(self.valor['outputs'][saida]['actions'])

    def get_valor_objeto(self, dicionario: dict, items: str|list):
        try:
            return reduce(lambda objeto, chave: objeto[chave], items, dicionario)
        except:
            return None


class evaluateScheduleGroup(Message):
    def __init__(self, ws: WebSocket, chave, valor, api: Genesys, fluxo) -> None:
        super().__init__(ws)
        self.chave = chave
        self.valor = valor
        self.api = api
        self.fluxo = fluxo
    
    async def enviar_mensagem(self):
        await self.fluxo.doc_genesys(self.valor['outputs']['open']['actions'])


class initializeFlowOutcome(Message):
    def __init__(self, ws: WebSocket, chave, valor, api: Genesys, fluxo) -> None:
        super().__init__(ws)
        self.chave = chave
        self.valor = valor
        self.api = api
        self.fluxo = fluxo
    
    async def enviar_mensagem(self):
        name = self.valor['name']
        name_flow_outcome = self.valor['flowOutcome']['name']
        await self.web_socket.send_json({self.chave: f'{name}: {name_flow_outcome}'})


class setFlowOutcome(Message):
    def __init__(self, ws: WebSocket, chave, valor, api: Genesys, fluxo) -> None:
        super().__init__(ws)
        self.chave = chave
        self.valor = valor
        self.api = api
        self.fluxo = fluxo
    
    async def enviar_mensagem(self):
        name = self.valor['name']
        name_flow_outcome = self.valor['flowOutcome']['name']
        value_flow_outcome = self.valor['flowOutcomeValue']
        await self.web_socket.send_json({self.chave: f'{name}: {name_flow_outcome} - {value_flow_outcome}'})


class setUUIData(Message):
    def __init__(self, ws: WebSocket, chave, valor, api: Genesys, fluxo) -> None:
        super().__init__(ws)
        self.chave = chave
        self.valor = valor
        self.api = api
        self.fluxo = fluxo
    
    async def enviar_mensagem(self):
        name = self.valor['name']
        mode = self.valor['mode']
        uui_data = self.valor['uuiData']['exp']
        await self.web_socket.send_json({self.chave: f'{name}: {mode} - {uui_data}'})


class transferToAcd(Message):
    def __init__(self, ws: WebSocket, chave, valor, api: Genesys, fluxo) -> None:
        super().__init__(ws)
        self.chave = chave
        self.valor = valor
        self.api = api
        self.fluxo = fluxo
    
    async def enviar_mensagem(self):
        self.fluxo.finaliza_loop = True
        name = self.valor['name']
        if self.valor['targetQueue'].get('lit'):
            name_queue = self.valor['targetQueue']['lit']['name']
        else:
            name_queue = await self.fluxo.trocar_variavel_pelo_valor(self.valor['targetQueue']['exp'])
        await self.web_socket.send_json({self.chave: f'{name}: {name_queue}'})

