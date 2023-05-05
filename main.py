import yaml
import time
from funcoes_genesys import *


def trocar_variavel_pelo_valor(texto: str):
    try:
        if 'Task' in texto or 'Flow' in texto:
            if texto in objetos_global.keys():
                return objetos_global[texto]
            
            if texto in objetos_tarefa.keys():
                return objetos_tarefa[texto]
            
            for chave, valor in objetos_global.items():
                if chave in texto:
                    texto = f'{texto.replace(chave, str(valor))}'

            for chave, valor in objetos_tarefa.items():
                if chave in texto:
                    texto = f'{texto.replace(chave, str(valor))}'

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


def doc_genesys(objeto, lista: list):
    finaliza_loop = False
    proxima_task = None
    try:
        if type(objeto) == list:
            for obj in objeto:
                _ , finaliza_loop, proxima_task = doc_genesys(obj, lista)
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
                            valor['audio']['exp'] = trocar_variavel_pelo_valor(valor['audio']['exp'])
                            print('Tocou o prompt: '+valor['audio']['exp'])
                    case 'setParticipantData':
                        for atributo in valor['attributes']:
                                atributo_name = atributo['attribute']['name']['lit'] if atributo['attribute']['name'].get('lit') else atributo['attribute']['name']['exp']
                                if atributo['attribute']['value'].get('exp'):
                                    atributo_value = atributo['attribute']['value']['exp']
                                    atributo_value = trocar_variavel_pelo_valor(atributo_value)
                                else:
                                    atributo_value = atributo['attribute']['value']['lit']             
                                print(f'Atributo {atributo_name} = {atributo_value}')
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
                        _ , finaliza_loop, proxima_task = doc_genesys(saida[chave]['actions'], lista)
                    case 'disconnect':
                        finaliza_loop = True
                        print(valor['name'])
                    case 'jumpToTask':
                        name_task = valor['name']
                        proxima_task = ref_task = valor['targetTaskRef']
                        print(f'{name_task} = {ref_task}\n')
                    case 'updateData':
                        name_data = valor['name']
                        for var in valor['statements']:
                            for chave, valor in var.items():
                                if valor['value'].get('lit') != None:
                                    valor_var = valor["value"]["lit"]
                                    if type(valor_var) == list:
                                        for var in  valor_var:
                                            valor_var = trocar_variavel_pelo_valor(str(var['exp']))
                                    if type(valor_var) == str:
                                        valor_var = f'"{trocar_variavel_pelo_valor(valor_var)}"'
                                else:
                                    valor_var = trocar_variavel_pelo_valor(valor['value']['exp'])
                                
                                definir_variavel_global_ou_local(valor['variable'], valor_var)
                                #print(f'{name_data} - {valor["variable"]}: {chave} = {valor_var}')
                    case 'setWrapupCode':
                        wrapup_code = valor['wrapupCode']['lit']['name']
                        print(f'wrapup_code = {wrapup_code}')
                    case 'switch':
                        for case in valor['evaluate']['firstTrue']['cases']:
                            exp = case['case']['value']['exp']
                            condition = trocar_variavel_pelo_valor(exp)
                            match condition:
                                case True:
                                    _ , finaliza_loop, proxima_task = doc_genesys(case['case']['actions'], lista)
                                    break
                                case False:
                                    continue
                                case _:
                                    acessar_case = input(f'condição: {condition} é verdadeira? yes/no ').lower()
                                    if acessar_case == 'yes':
                                        _ , finaliza_loop, proxima_task = doc_genesys(case['case']['actions'], lista)
                                        break
                        else:
                            _ , finaliza_loop, proxima_task = doc_genesys(valor['evaluate']['firstTrue']['default']['actions'], lista)
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
                            _ , finaliza_loop, proxima_task = doc_genesys(valor['outputs']['success']['actions'], lista)
                        else:
                            _ , finaliza_loop, proxima_task = doc_genesys(valor['outputs']['failure']['actions'], lista)
                    case 'loop':
                        var_loop = valor['currentIndex']['var']
                        count_loop = valor['loopCount']['lit']
                        for index in range(count_loop):
                            definir_variavel_global_ou_local(var_loop, index)
                            _ , finaliza_loop, proxima_task = doc_genesys(valor['outputs']['loop']['actions'], lista)
                            if finaliza_loop:
                                finaliza_loop = False
                                break
                            else:
                                continue
                    case 'loopExit':
                        finaliza_loop = True
                    case 'loopNext':
                        finaliza_loop = False    
                    case _:
                        print(chave, valor)
                        if type(valor) == list or type(valor) == dict:
                            _ , finaliza_loop, proxima_task = doc_genesys(valor, lista) 
        return lista, finaliza_loop, proxima_task
    except Exception as erro:
        print('ERRO')
        print(erro)
        print(objeto)
        exit()

        
with open('PSAT_Clube_v5a_v4-0.yaml', "r", encoding="utf-8") as arquivo:
    data = yaml.safe_load(arquivo)


objetos_global = criar_variaveis(data['inboundCall']['variables'])
tasks = {f'/inboundCall/tasks/task[{task["task"]["refId"]}]': task['task'] for task in data['inboundCall']['tasks']}
task_loop = data['inboundCall']['tasks'][0]['task']

while True:
    objetos_tarefa = criar_variaveis(task_loop['variables']) if 'variables' in task_loop.keys() else {}
    
    for objeto in task_loop['actions']:
        lista, finaliza_loop, proxima_task = doc_genesys(objeto, [])
        for item in lista:
            print(item)
        if proxima_task != None:
            if tasks[proxima_task] != task_loop:
                objetos_tarefa.clear()
            task_loop = tasks[proxima_task]
            break
        if finaliza_loop:
            exit()
                
