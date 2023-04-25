import yaml

def quebrar_dicionario(objeto, lista: list):
    try:
        if type(objeto) == list:
            for obj in objeto:
                quebrar_dicionario(obj, lista)
        elif type(objeto) == dict:
            for chave, valor in objeto.items():
                match chave:
                    case 'transferToFlow':
                        lista.extend(['Transferindo para o fluxo: '+valor['targetFlow']['name']])
                    case 'playAudio':
                        if valor['audio'].get('prompt'):
                            lista.extend(['Tocou o prompt: '+valor['audio']['prompt']])
                        elif valor['audio'].get('tts'):
                            lista.extend(['Tocou o prompt: '+valor['audio']['tts']])
                        else:
                            lista.extend(['Tocou o prompt: '+valor['audio']['exp']])
                    case 'setParticipantData':
                        if len(valor['attributes']) == 1:
                            atributo_name = valor['attributes'][0]['attribute']['name']['lit']
                            atributo_value = valor['attributes'][0]['attribute']['value']['exp']
                            atributo_value = objetos_global[atributo_value] if atributo_value in objetos_global.keys() else atributo_value
                            lista.extend([f'Atributo {atributo_name} = {atributo_value}'])
                        else:
                            for atributo in valor['attributes']:
                                print(atributo)
                    case 'decision':
                        condition = valor['condition']['exp']
                        name = valor['name']
                        saida = valor.get('outputs')
                        if saida is None:
                            raise Exception(f'erro decision {name}: {chave} = {valor}, {acao}')
                        chave = input(f'yes/no\ncondição: {condition} é verdadeira? ').lower()
                        quebrar_dicionario(saida[chave]['actions'], lista)
                    case 'disconnect':
                        lista.extend([valor['name']])
                    case 'jumpToTask':
                        name_task = valor['name']
                        ref_task = valor['targetTaskRef']
                        lista.extend([f'{name_task} = {ref_task}'])
                    case 'updateData':
                        name_data = valor['name']
                        auxiliar = []
                        for var in valor['statements']:
                            for chave, valor in var.items():
                                valor_var = valor['value']['lit'] if valor['value'].get('lit') != None else valor['value']['exp']
                                auxiliar.append([chave, valor['variable'], valor_var])
                        for tipo_var, nome_var, valor_var in auxiliar:
                            objetos_global[nome_var] = valor_var
                            lista.extend([f'{name_data} - {nome_var}: {tipo_var} = {valor_var}'])
                    case 'setWrapupCode':
                        wrapup_code = valor['wrapupCode']['lit']['name']
                        lista.extend([f'wrapup_code = {wrapup_code}'])
                    case 'switch':
                        for case in valor['evaluate']['firstTrue']['cases']:
                            exp = case['case']['value']['exp']
                            lista.extend([f'case {exp}'])
                            quebrar_dicionario(case['case']['actions'], lista)
                    case 'collectInput':
                        prompt = valor['inputAudio']['prompt'] if valor['inputAudio'].get('prompt') else valor['inputAudio']['tts']
                        print(f'Tocou o prompt: {prompt}')
                        name_var = valor['inputData']['var']
                        value_var = input(f'Digite a entrada: ')
                        objetos_global[name_var] = value_var
                        lista.extend([f'{name_var} = "{value_var}"'])
                        if value_var != "":
                            quebrar_dicionario(valor['outputs']['success']['actions'], lista)
                        else:
                            quebrar_dicionario(valor['outputs']['failure']['actions'], lista)
                    case _:
                        print(chave, valor)
                        if type(valor) == list or type(valor) == dict:
                            quebrar_dicionario(valor, lista) 
        return lista
    except Exception as erro:
        print('ERRO')
        print(erro)
        print(objeto)
        exit()


with open('Testes_Matheus_v2-0.yaml', "r", encoding="utf-8") as arquivo:
    data = yaml.safe_load(arquivo)


objetos_global = {}

for task in data['inboundCall']['tasks']:
    for acao in task['task']['actions']:
        lista = quebrar_dicionario(acao, [])
        match len(lista):
            case 0:
                pass
                #print(f'lista vazia pela ação: {acao}')
            case _:
                for task in lista:
                    print(task)
        
