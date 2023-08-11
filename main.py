from fastapi import FastAPI, status, HTTPException, UploadFile, WebSocket, Cookie, WebSocketException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
import yaml
from model.Menu import Menu, Genesys

app = FastAPI()
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory='templates')
api_genesys, file_genesys, attribute, objetos_globais, objetos_tarefa = (None, None, {}, {}, {})

@app.get('/', response_class=HTMLResponse, tags=['SITE'])
def index(resquest: Request, mensagem: str = Cookie(default="")):
    context = {
        "request": resquest,
        "arquivo": "/index.css",
        "mensagem": mensagem
    }
    response = templates.TemplateResponse('index.html', context=context)
    response.set_cookie(key='mensagem', value='')
    return response

@app.get('/tests', response_class=HTMLResponse, tags=['SITE'])
def testing_flow(resquest: Request, mensagem: str = Cookie(default="")):
    api_genesys = Genesys()
    if file_genesys and api_genesys:
        context = {
            "request": resquest,
            "arquivo": "/testing.css",
            "mensagem": mensagem
        }
        response = templates.TemplateResponse('testing.html', context=context)
        response.set_cookie(key='mensagem', value='')
        return response
    else:
        mensagem = 'Falha ao iniciar os testes. Verifique o arquivo YAML e o token Genesys'
        response = RedirectResponse(url='/', status_code=status.HTTP_303_SEE_OTHER, headers={"Referer": "/tests"})
        response.set_cookie('mensagem',mensagem)
        return response

@app.get('/file', tags=['API'])
async def get_file():
    global file_genesys
    if file_genesys:
        dados = yaml.safe_load(file_genesys)
        return dados
    else:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Nenhum Arquivo foi adicionado')
    
@app.post('/file', tags=['API'])
async def alterar_arquivo(file: UploadFile):
    global file_genesys
    try:
        assert '.yaml' in file.filename
        file_genesys = await file.read()
        mensagem, rota = ('Arquivo recebido com sucesso','/tests')
    except:
        mensagem, rota = ('Falha no arquivo recebido','/')
    finally:
        response = RedirectResponse(url=rota, status_code=status.HTTP_303_SEE_OTHER, headers={"Referer": "/file"})
        response.set_cookie('mensagem',mensagem)
        return response

@app.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    api_genesys = Genesys()
    data = yaml.safe_load(file_genesys)
    try:
        menu = Menu(websocket, api_genesys, data)
        await menu.loop_main()
    except WebSocketException as erro:
        print('Websockert erro:', erro)
    except Exception as erro:
        print('Exception erro:', erro)
        await websocket.send_json({"Erro":erro})
    finally:
        await websocket.close()
    