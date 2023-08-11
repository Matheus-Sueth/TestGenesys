import requests
import os
import base64
import json
import time
from dotenv import load_dotenv
from .Prompt import Prompt

load_dotenv()

class Genesys:
    URL_AUTH = os.environ.get('URL_AUTH')
    URL = os.environ.get('URL')
    CLIENT_ID = os.environ.get('CLIENT_ID')
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

    def __init__(self) -> None:
        self.token = self.get_token()
        self.verificar_token()

    def __new__(self, *args):
        if not hasattr(self, 'instance'):
            self.instance = super(Genesys, self).__new__(self)
        return self.instance

    def atualizar_token(self):
        self.token = self.get_token()

    def get_token(self) -> str:
        authorization = base64.b64encode(bytes(self.CLIENT_ID + ":" + self.CLIENT_SECRET, "ISO-8859-1")).decode("ascii")

        request_headers = {
            "Authorization": f"Basic {authorization}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        request_body = {
            "grant_type": "client_credentials"
        }

        response = requests.post(f"https://login.{self.URL_AUTH}/oauth/token", data=request_body, headers=request_headers)

        if response.ok:
            response_json = response.json()
            return response_json['access_token']
        else:
            raise Exception(f"Failure: {response.status_code} - {response.reason}")
    
    def verificar_token(self) -> None:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"bearer {self.token}"
        }
        response = requests.head(url='https://'+self.URL+'/api/v2/tokens/me', headers=headers)
        if not response.ok:
            raise Exception(f'Token Genesys inválido, failure: {response.status_code} - {response.reason}')
        return None
 
    def procurar_prompt(self, name_prompt: str) -> Prompt:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"bearer {self.token}"
        }
        result = requests.get(url='https://'+self.URL+f'/api/v2/architect/prompts?name={name_prompt}', headers=headers)
        dados = result.json()
        if not result.ok:
            raise Exception(f'Falha na chamada(procurar_prompt({name_prompt})), status: {result.status_code}, json: {dados}')
        if dados['total'] != 1:
            raise Exception(f'Falha na chamada(procurar_prompt({name_prompt})), status: {result.status_code}, json: {dados}')
        entitie = dados['entities'][0]
        return Prompt(entitie)

    def procurar_data_table(self, name_data_table: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"bearer {self.token}"
        }
        result = requests.get(url='https://'+self.URL+f'/api/v2/flows/datatables/divisionviews?name={name_data_table}', headers=headers)
        dados = result.json()
        if not result.ok:
            raise Exception(f'Falha na chamada(procurar_data_table({name_data_table})), status: {result.status_code}, json: {dados}')
        if dados['total'] != 1:
            raise Exception(f'Falha na chamada(procurar_data_table({name_data_table})), status: {result.status_code}, json: {dados}')
        return dados['entities'][0]['id']
    
    def procurar_row_data_table(self, data_table_id: str, key: str) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"bearer {self.token}"
        }
        result = requests.get(url='https://'+self.URL+f'/api/v2/flows/datatables/{data_table_id}/rows/{key}?showbrief=false', headers=headers)
        dados = result.json()
        if result.status_code != 200 and result.status_code != 404:
            raise Exception(f'Falha na chamada(procurar_row_data_table({data_table_id}, {key})), status: {result.status_code}, json: {dados}')
        return dados
    
    def procurar_data_action(self, category_name: str, name_data_action: str) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"bearer {self.token}"
        }
        result = requests.get(url='https://'+self.URL+f'/api/v2/integrations/actions?category={category_name}&name={name_data_action}', headers=headers)
        dados = result.json()
        if result.status_code != 200 and len(dados['entities']) == 0:
            raise Exception(f'Falha na chamada(procurar_data_action({category_name}, {name_data_action})), status: {result.status_code}, json: {dados}')
        return dados['entities'][0]

    def executar_data_action(self, data_action_id: str, body: dict, tempo_timeout: int) -> tuple[dict, str]:
        status = ''
        dados = ''
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"bearer {self.token}"
            }
            result = requests.post(url='https://'+self.URL+f'/api/v2/integrations/actions/{data_action_id}/test', headers=headers, data=json.dumps(body), timeout=tempo_timeout)
            status = result.status_code
            dados = result.json()
            if result.ok:
                return (dados, 'success')
            elif status == 408 or status == 504:
                return (dados, 'timeout')
            return (dados, 'failure')
        except requests.exceptions.ReadTimeout:
            return ({},'timeout')
        except Exception as erro:
            raise Exception(f'Falha na chamada(executar_data_action({data_action_id}), status: {status}, json: {dados}, erro: {erro}')

