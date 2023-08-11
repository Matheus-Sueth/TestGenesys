from fastapi import WebSocket

class Message:
    def __init__(self, ws: WebSocket) -> None:
        self.web_socket = ws