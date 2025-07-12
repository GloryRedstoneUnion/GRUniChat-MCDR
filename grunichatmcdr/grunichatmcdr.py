# MCDR GRUniChatMCDR 插件入口
from mcdreforged.api.all import *
from grunichatmcdr.config import GRUniChatConfig
from grunichatmcdr.core.main import start_ws_service, stop_ws_service
from grunichatmcdr.cmd.command_tree import register_grunichat_command
from grunichatmcdr.core.websocket_service import WebSocketService
import os
import json
import time
import uuid


def on_info(server: PluginServerInterface, info):
    global _ws_service
    # 检查 WebSocket 是否连接
    if _ws_service and _ws_service.ws and _ws_service.ws.sock and _ws_service.ws.sock.connected:
        msg = None
        # 聊天消息
        if info.is_player and info.player:
            msg = _ws_service._create_message(
                msg_type="chat",
                sender=info.player,
                chat_message=info.content
            )
        # 进服
        elif info.content.endswith("joined the game"):
            player = info.content.replace("joined the game", "").strip()
            msg = _ws_service._create_message(
                msg_type="event",
                event_detail=f"{player} joined the game"
            )
        # 退服
        elif info.content.endswith("left the game"):
            player = info.content.replace("left the game", "").strip()
            msg = _ws_service._create_message(
                msg_type="event",
                event_detail=f"{player} left the game"
            )
        # 其它 info 不转发
        if msg is not None:
            try:
                _ws_service.ws.send(json.dumps(msg))
                server.logger.info(f"WebSocket已转发: {msg}")
            except Exception as e:
                server.logger.error(f"WebSocket转发消息失败: {e}")
    else:
        server.logger.warning("WebSocket未连接，info未转发")

_ws_service = None

def on_load(server: PluginServerInterface, old):
    global _ws_service
    server.logger.info('GRUniChatMCDR 插件已加载，尝试建立WebSocket连接')
    config = server.load_config_simple(target_class=GRUniChatConfig)
    _ws_service = start_ws_service(server, config)
    register_grunichat_command(server, _ws_service, config=None)
    server.register_event_listener('info', on_info)

def on_server_startup(server: PluginServerInterface):
    global _ws_service
    server.logger.info('GRUniChatMCDR 服务器已启动')
    # 向 WebSocket 发送服务器已启动通知
    if _ws_service and _ws_service.ws and _ws_service.ws.sock and _ws_service.ws.sock.connected:
        try:
            msg = _ws_service._create_message(
                msg_type="event",
                event_detail="MCDR 服务器已启动"
            )
            _ws_service.ws.send(json.dumps(msg))
            server.logger.info("WebSocket已通知服务器启动")
        except Exception as e:
            server.logger.error(f"WebSocket发送服务器启动通知失败: {e}")

def on_unload(server: PluginServerInterface):
    global _ws_service
    # 向 WebSocket 发送插件卸载通知
    if _ws_service and _ws_service.ws and _ws_service.ws.sock and _ws_service.ws.sock.connected:
        try:
            msg = _ws_service._create_message(
                msg_type="event",
                event_detail="GRUniChatMCDR 插件被卸载"
            )
            _ws_service.ws.send(json.dumps(msg))
            server.logger.info("WebSocket已通知插件卸载")
        except Exception as e:
            server.logger.error(f"WebSocket发送插件卸载通知失败: {e}")
    stop_ws_service()
