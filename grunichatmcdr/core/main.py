from .websocket_service import WebSocketService

_ws_service = None

def start_ws_service(server, config):
    global _ws_service
    _ws_service = WebSocketService(server, config)
    _ws_service.start()
    return _ws_service

def stop_ws_service():
    global _ws_service
    if _ws_service:
        _ws_service.stop()
        _ws_service = None
