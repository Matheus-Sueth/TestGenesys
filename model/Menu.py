import re
from pyparsing import Word, alphas, alphanums, Literal, Forward, opAssoc, infixNotation, nums, delimitedList
from .Message import Message
from .Functions import *
from .Genesys import Genesys
from .Actions import *
from .Variable import *


class Menu(Message):
    global my_functions
    lista_funcoes = my_functions
    objetos_global, objetos_tarefa, attribute = Flow(), Task(), Attributte()
    finaliza_loop, proxima_task = False, None

    def __init__(self, ws, api: Genesys, dados: dict) -> None:
        super().__init__(ws)
        self.api_genesys = api
        self.fluxo_genesys = dados

    async def loop_main(self) -> None:
        for variavel in self.fluxo_genesys['inboundCall']['variables']:
            for valor in variavel.values():
                variavel_value = None if valor['initialValue'].get('noValue') else valor['initialValue']['lit']
                variavel_name = valor['name'].split('.')
                self.objetos_global.definir_dados(**{variavel_name[1]: variavel_value})
        tasks = {f'/inboundCall/tasks/task[{task["task"]["refId"]}]': task['task'] for task in self.fluxo_genesys['inboundCall']['tasks']}
        task_loop = tasks[self.fluxo_genesys['inboundCall']['startUpRef']]
        while not self.finaliza_loop:
            if 'variables' in task_loop.keys():
                for variavel in task_loop['variables']:
                    for valor in variavel.values():
                        variavel_value = None if valor['initialValue'].get('noValue') else valor['initialValue']['lit']
                        variavel_name = valor['name'].split('.')
                        self.objetos_tarefa.definir_dados(**{variavel_name[1]: variavel_value})

            for objeto in task_loop['actions']:
                await self.doc_genesys(objeto)
                if self.proxima_task:
                    if tasks[self.proxima_task] != task_loop:
                        self.objetos_tarefa.clear_dados()
                    task_loop = tasks[self.proxima_task]
                    self.proxima_task = ''
                    break

                if self.finaliza_loop:
                    break
        print(vars(self.attribute))

    async def trocar_variavel_pelo_valor(self, texto: str):
        auxiliar_texto = texto 
        auxiliar_texto = auxiliar_texto.replace('_','')
        if texto.strip() == '' or auxiliar_texto.isalpha():
            return texto
        auxiliar_texto = texto
        auxiliar_texto = auxiliar_texto.replace('\n','')
        auxiliar_texto = auxiliar_texto.replace('\t',' ')        
        try:
            if 'true' in texto:
                auxiliar_texto = texto.replace('true','True')
            if 'false' in texto:
                auxiliar_texto = auxiliar_texto.replace('false','False')
            if 'NOT_SET' in texto:
                auxiliar_texto = auxiliar_texto.replace('NOT_SET','None')
            if '!' in texto:
                auxiliar_texto = re.sub(r'(?<!=)!(?!=)', 'not ', auxiliar_texto)
            if 'Task' in texto:
                auxiliar_texto = auxiliar_texto.replace('Task','self.objetos_tarefa')
            if 'Flow' in texto:
                auxiliar_texto = auxiliar_texto.replace('Flow','self.objetos_global')
            if 'Prompt.' in texto:
                regex = r"\b" + re.escape('Prompt.') + r"\b"
                auxiliar_texto = re.sub(regex, 'Prompt.', '', flags=re.I)
            if 'AND' in texto or 'OR' in texto:
                auxiliar_texto = auxiliar_texto.replace('AND','and')
                auxiliar_texto = auxiliar_texto.replace('OR','or')

            for funcao in self.lista_funcoes:
                regex = r"\b" + re.escape(funcao) + r"\b"
                auxiliar_texto = re.sub(regex, funcao, auxiliar_texto, flags=re.I)

            

            try:
                if '?' in texto and ':' in texto:
                    while re.search(r'\?.*\:', auxiliar_texto):
                        condicao, sucesso, falha = map(str.strip, re.split(r'\?|:', auxiliar_texto, maxsplit=2))
                        print(f'\n----- condicao: {condicao} -- sucesso: {sucesso} -- falha: {falha}-------\n')
                        if condicao[0] == '(' and condicao[-1] == ')':
                            condicao = condicao[1:-1]
                        if eval(condicao):
                            auxiliar_texto = sucesso
                        else:
                            auxiliar_texto = falha
                    texto = auxiliar_texto
                else:
                    texto = eval(auxiliar_texto)
            except Exception as erro:
                print(f'\nFlow: {self.objetos_global.__dict__}\nTask: {self.objetos_tarefa.__dict__}\n')
                print(f'Erro na função trocar_variavel_pelo_valor: {erro}\nTexto: {texto}\nAuxiliar Texto: {auxiliar_texto}')
            finally:
                return texto
        except Exception as erro:
            raise Exception(f'Erro na função trocar_variavel_pelo_valor: {erro} - texto: {texto}')

    async def definir_variavel_global_ou_local(self, variavel: str, valor: object) -> None:
        atributo_name = variavel.split('.')
        if 'Task' not in variavel and 'Flow' not in variavel:
            raise Exception(f'Falha na função definir_variavel_global_ou_local com a variavel: {variavel}') 
        if 'Task' in variavel:
            self.objetos_tarefa.definir_dados(**{atributo_name[1]: valor})
        if 'Flow' in variavel:
            self.objetos_global.definir_dados(**{atributo_name[1]: valor})
        return None

    async def doc_genesys(self, objeto_tarefa) -> None:
        if type(objeto_tarefa) == list:
            for sub_objeto_tarefa in objeto_tarefa:
                await self.doc_genesys(sub_objeto_tarefa)
        elif type(objeto_tarefa) == dict:
            for chave, valor in objeto_tarefa.items():
                match chave:
                    case 'transferToFlow':
                        action = transferToFlow(chave, valor, self.web_socket)
                        await action.enviar_mensagem()
                    case 'playAudio':
                        action = playAudio(chave, valor, self.api_genesys, self.web_socket, self)
                        await action.enviar_mensagem()
                    case 'setParticipantData':
                        action = setParticipantData(self.web_socket, chave, valor, self)
                        await action.enviar_mensagem()
                    case 'getParticipantData':
                        action = getParticipantData(self.web_socket, chave, valor, self)
                        await action.enviar_mensagem()
                    case 'decision':
                        action = decision(self.web_socket, chave, valor, self, objeto_tarefa)
                        await action.enviar_mensagem()
                    case 'disconnect':
                        action = disconnect(self.web_socket, chave, valor, self)
                        await action.enviar_mensagem()
                        return None
                    case 'jumpToTask':
                        action = jumpToTask(self.web_socket, chave, valor, self)
                        await action.enviar_mensagem()
                        return None
                    case 'updateData':
                        action = updateData(self.web_socket, chave, valor, self)
                        await action.enviar_mensagem()
                    case 'setWrapupCode':
                        action = setWrapupCode(self.web_socket, chave, valor)
                        await action.enviar_mensagem()
                    case 'switch':
                        action = switch(self.web_socket, chave, valor, self)
                        await action.enviar_mensagem()
                    case 'collectInput': 
                        action = collectInput(self.web_socket, chave, valor, self)
                        await action.enviar_mensagem()
                    case 'loop':
                        action = loop(self.web_socket, chave, valor, self)
                        await action.enviar_mensagem()
                    case 'loopExit':
                        self.finaliza_loop = True
                    case 'loopNext':
                        self.finaliza_loop = False    
                    case 'dataTableLookup':
                        action = dataTableLookup(self.web_socket, chave, valor, self.api_genesys, self)
                        await action.enviar_mensagem()
                    case 'callData':
                        action = callData(self.web_socket, chave, valor, self.api_genesys, self)
                        await action.enviar_mensagem()
                    case 'evaluateScheduleGroup':
                        action = evaluateScheduleGroup(self.web_socket, chave, valor, self.api_genesys, self)
                        await action.enviar_mensagem()
                    case 'initializeFlowOutcome':
                        action = initializeFlowOutcome(self.web_socket, chave, valor, self.api_genesys, self)
                        await action.enviar_mensagem()
                    case 'setFlowOutcome':
                        action = setFlowOutcome(self.web_socket, chave, valor, self.api_genesys, self)
                        await action.enviar_mensagem()
                    case 'setUUIData':
                        action = setUUIData(self.web_socket, chave, valor, self.api_genesys, self)
                        await action.enviar_mensagem()
                    case 'transferToAcd':
                        action = transferToAcd(self.web_socket, chave, valor, self.api_genesys, self)
                        await action.enviar_mensagem()
                        return None
                    case _:
                        await self.web_socket.send_json(objeto_tarefa)
                        if type(valor) == list or type(valor) == dict:
                            await self.doc_genesys(valor)
