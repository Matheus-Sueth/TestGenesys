import yaml

def quebrar_dicionario(objeto, lista: list):
    try:
        if type(objeto) == list:
            for obj in objeto:
                quebrar_dicionario(obj, lista)
        elif type(objeto) == dict:
            for chave, valor in objeto.items():
                if chave == 'transferToFlow':
                    lista.extend(['Transferindo para o fluxo: '+valor['targetFlow']['name']])
                elif chave == 'playAudio':
                    if valor['audio'].get('prompt'):
                        lista.extend(['Tocou o prompt: '+valor['audio']['prompt']])
                        #lista.extend(['Tocou o prompt: '+valor['audio']['prompt']])
                    else:
                        lista.extend(['Tocou o prompt: '+valor['audio']['exp']])
                        #lista.extend(['Tocou o prompt: '+valor['audio']['exp']])
                elif chave == 'setParticipantData':
                    if len(valor['attributes']) == 1:
                        atributo_name = valor['attributes'][0]['attribute']['name']['lit']
                        atributo_value = valor['attributes'][0]['attribute']['value']['exp']
                        lista.extend([f'Atributo {atributo_name} = {atributo_value}'])
                    else:
                        for atributo in valor['attributes']:
                            print(atributo)
                elif chave == 'decision':
                    condition = valor['condition']['exp']
                    name = valor['name']
                    lista.extend([f'condição = {condition}'])
                    saida = valor.get('outputs')
                    if saida is None:
                        raise Exception(f'erro decision {name}: {chave} = {valor}, {acao}')
                    for chave, valor in saida.items():
                        lista.extend([f'{name}: {chave}'])
                        quebrar_dicionario(valor['actions'], lista)
                elif chave == 'disconnect':
                    lista.extend([valor['name']])
                elif chave == 'setWrapupCode':
                    wrapup_code = valor['wrapupCode']['lit']['name']
                    lista.extend([f'wrapup_code = {wrapup_code}'])
                elif chave == 'switch':
                    for case in valor['evaluate']['firstTrue']['cases']:
                        exp = case['case']['value']['exp']
                        lista.extend([f'case {exp}'])
                        quebrar_dicionario(case['case']['actions'], lista)
                elif chave == 'collectInput':
                    prompt = valor['inputAudio']['prompt'] if valor['inputAudio'].get('prompt') else valor['inputAudio']['tts']
                    print(f'Tocou o prompt: {prompt}')
                    #lista.extend(['Tocou o prompt: '+valor['inputAudio']['prompt']])
                    value_var = input(f'Opção do {prompt}: ')
                    name_var = valor['inputData']['var']
                    lista.extend([f'Opção digitada foi: {value_var}',f'{name_var} = "{value_var}"'])
                    quebrar_dicionario(valor['outputs']['success']['actions'], lista)
                else:
                    print(chave, valor)
                    if type(valor) == list or type(valor) == dict:
                        quebrar_dicionario(valor, lista) 
        return lista
    except Exception as erro:
        print('ERRO')
        print(erro)
        print(objeto)
        exit()


with open('teste.yaml', "r", encoding="utf-8") as arquivo:
    data = yaml.safe_load(arquivo)

acoes = data['inboundCall']['tasks'][8]['task']['actions']
for acao in acoes:
    lista = quebrar_dicionario(acao, [])
    match len(lista) :
        case 0:
            pass
            #print(f'lista vazia pela ação: {acao}')
        case _:
            print(lista)
        
