import yaml
from funcoes_genesys import *


def trocar_variavel_pelo_valor(texto: str):
    try:
        if texto in objetos_global.keys():
            return objetos_global[texto]
        
        if texto in objetos_tarefa.keys():
            return objetos_tarefa[texto]
        
        for chave in objetos_global.keys():
            if chave in texto:
                texto = f'({texto.replace(chave, str(objetos_global[chave]))})'

        for chave in objetos_tarefa.keys():
            if chave in texto:
                texto = f'({texto.replace(chave, str(objetos_tarefa[chave]))})'

        palavras = texto.split()

        for palavra in palavras:
            if palavra in objetos_global.keys():
                texto = f'({texto.replace(palavra, str(objetos_global[palavra]))})'

            if palavra in objetos_tarefa.keys():
                texto = f'({texto.replace(palavra, str(objetos_tarefa[palavra]))})'

        try:
            texto = eval(texto)
        finally:
            return texto
    except Exception as erro:
        raise Exception(f'Erro na função trocar_variavel_pelo_valor: {erro}')


def definir_variavel_global_ou_local(variavel: str, valor: object) -> None:
    if 'Task' in variavel:
        objetos_tarefa[variavel] = valor
    else:
        objetos_global[variavel] = valor
    return None


def criar_variaveis(lista_variaveis: list) -> dict:
    objetos = {}
    for variavel in lista_variaveis:
        for valor in variavel.values():
            objetos[valor['name']] = None if valor['initialValue'].get('noValue') else valor['initialValue']['lit']
    return objetos


def quebrar_dicionario(objeto, lista: list):
    finaliza_loop = False
    proxima_task = None
    try:
        if type(objeto) == list:
            for obj in objeto:
                _ , finaliza_loop, proxima_task = quebrar_dicionario(obj, lista)
        elif type(objeto) == dict:
            for chave, valor in objeto.items():
                match chave:
                    case 'transferToFlow':
                        print('Transferindo para o fluxo: '+valor['targetFlow']['name'])
                    case 'playAudio':
                        if valor['audio'].get('prompt'):
                            print('Tocou o prompt: '+valor['audio']['prompt'])
                        elif valor['audio'].get('tts'):
                            print('Tocou o prompt: '+valor['audio']['tts'])
                        else:
                            print('Tocou o prompt: '+valor['audio']['exp'])
                    case 'setParticipantData':
                        if len(valor['attributes']) == 1:
                            atributo_name = valor['attributes'][0]['attribute']['name']['lit']
                            atributo_value = valor['attributes'][0]['attribute']['value']['exp']
                            atributo_value = trocar_variavel_pelo_valor(atributo_value)
                            print(f'Atributo {atributo_name} = {atributo_value}')
                        else:
                            for atributo in valor['attributes']:
                                print(atributo)
                    case 'decision':
                        condition = valor['condition']['exp']  
                        condition = trocar_variavel_pelo_valor(condition)
                        name = valor['name']
                        saida = valor.get('outputs')
                        if saida is None:
                            raise Exception(f'erro decision {name}: {chave} = {valor}, {objeto}')
                        match condition:
                            case True:
                                chave = 'yes'
                            case False:
                                chave = 'no'
                            case _:
                                chave = input(f'condição: {condition} é verdadeira? yes/no ').lower()
                        _ , finaliza_loop, proxima_task = quebrar_dicionario(saida[chave]['actions'], lista)
                    case 'disconnect':
                        finaliza_loop = True
                        print(valor['name'])
                    case 'jumpToTask':
                        name_task = valor['name']
                        proxima_task = ref_task = valor['targetTaskRef']
                        print(f'{name_task} = {ref_task}\n')
                    case 'updateData':
                        name_data = valor['name']
                        auxiliar = []
                        for var in valor['statements']:
                            for chave, valor in var.items():
                                valor_var = valor['value']['lit'] if valor['value'].get('lit') != None else valor['value']['exp']
                                auxiliar.append([chave, valor['variable'], valor_var])
                        for tipo_var, nome_var, valor_var in auxiliar:
                            if type(valor_var) == str:
                                valor_var = trocar_variavel_pelo_valor(valor_var)
                            definir_variavel_global_ou_local(nome_var, valor_var)
                            print(f'{name_data} - {nome_var}: {tipo_var} = {valor_var}')
                    case 'setWrapupCode':
                        wrapup_code = valor['wrapupCode']['lit']['name']
                        print(f'wrapup_code = {wrapup_code}')
                    case 'switch':
                        for case in valor['evaluate']['firstTrue']['cases']:
                            exp = case['case']['value']['exp']
                            condition = trocar_variavel_pelo_valor(exp)
                            match condition:
                                case True:
                                    _ , finaliza_loop, proxima_task = quebrar_dicionario(case['case']['actions'], lista)
                                    break
                                case False:
                                    continue
                                case _:
                                    acessar_case = input(f'condição: {condition} é verdadeira? yes/no ').lower()
                                    if acessar_case == 'yes':
                                        _ , finaliza_loop, proxima_task = quebrar_dicionario(case['case']['actions'], lista)
                                        break
                        else:
                            _ , finaliza_loop, proxima_task = quebrar_dicionario(valor['evaluate']['firstTrue']['default']['actions'], lista)
                    case 'collectInput': 
                        if valor['inputAudio'].get('prompt'):
                            prompt = valor['inputAudio']['prompt']
                        elif valor['inputAudio'].get('tts'):
                            prompt = valor['inputAudio']['tts']
                        else:
                            prompt = valor['inputAudio']['exp']
                        prompt = trocar_variavel_pelo_valor(prompt)
                        print(f'\nTocou o prompt: {prompt}')
                        name_var = valor['inputData']['var']
                        value_var = input(f'Digite a entrada: ')
                        definir_variavel_global_ou_local(name_var, f'"{value_var}"')
                        if value_var != "":
                            _ , finaliza_loop, proxima_task = quebrar_dicionario(valor['outputs']['success']['actions'], lista)
                        else:
                            _ , finaliza_loop, proxima_task = quebrar_dicionario(valor['outputs']['failure']['actions'], lista)
                    case 'loop':
                        var_loop = valor['currentIndex']['var']
                        count_loop = valor['loopCount']['lit']
                        for index in range(count_loop):
                            definir_variavel_global_ou_local(var_loop, index)
                            _ , finaliza_loop, proxima_task = quebrar_dicionario(valor['outputs']['loop']['actions'], lista)
                            
                    case _:
                        print(chave, valor)
                        if type(valor) == list or type(valor) == dict:
                            _ , finaliza_loop, proxima_task = quebrar_dicionario(valor, lista) 
        return lista, finaliza_loop, proxima_task
    except Exception as erro:
        print('ERRO')
        print(erro)
        print(objeto)
        exit()


with open('Testes_Matheus_v3-0.yaml', "r", encoding="utf-8") as arquivo:
    data = yaml.safe_load(arquivo)


objetos_global = criar_variaveis(data['inboundCall']['variables'])
tasks = {f'/inboundCall/tasks/task[{task["task"]["refId"]}]': task['task'] for task in data['inboundCall']['tasks']}
task_loop = data['inboundCall']['tasks'][0]['task']


while True:
    objetos_tarefa = criar_variaveis(task_loop['variables'])
    for objeto in task_loop['actions']:
        lista, finaliza_loop, proxima_task = quebrar_dicionario(objeto, [])
        for item in lista:
            print(item)
        if proxima_task != None:
            if tasks[proxima_task] != task_loop:
                objetos_tarefa.clear()
            task_loop = tasks[proxima_task]
            break
        if finaliza_loop:
            exit()
                
