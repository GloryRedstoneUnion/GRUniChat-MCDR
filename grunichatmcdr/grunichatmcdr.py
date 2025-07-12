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
            _ws_service.send_message(
                msg_type="chat",
                sender=info.player,
                chat_message=info.content
            )
        # 玩家命令 - 格式: [玩家名: 命令结果]
        elif info.content.startswith("[") and ":" in info.content and info.content.endswith("]"):
            # 解析命令信息
            command_info = info.content[1:-1]  # 去掉方括号
            if ":" in command_info:
                player_part, command_result = command_info.split(":", 1)
                player_name = player_part.strip()
                command_desc = command_result.strip()
                _ws_service.send_message(
                    msg_type="event",
                    event_detail=f"Player {player_name} executed command: {command_desc}"
                )
    else:
        # 只在调试模式下输出此警告
        pass

def on_player_joined(server: PluginServerInterface, player: str, info: Info):
    """玩家加入服务器事件处理"""
    global _ws_service
    config = server.load_config_simple(target_class=GRUniChatConfig)
    if _ws_service and _ws_service.ws and _ws_service.ws.sock and _ws_service.ws.sock.connected:
        try:
            _ws_service.send_message(
                msg_type="event",
                event_detail=f"{player} joined the game"
            )
            server.logger.info(f"[{config.plugin_id}] 玩家加入事件已发送: {player}")
        except Exception as e:
            server.logger.error(f"[{config.plugin_id}] 发送玩家加入事件失败: {e}")

def on_player_left(server: PluginServerInterface, player: str):
    """玩家离开服务器事件处理"""
    global _ws_service
    config = server.load_config_simple(target_class=GRUniChatConfig)
    if _ws_service and _ws_service.ws and _ws_service.ws.sock and _ws_service.ws.sock.connected:
        try:
            _ws_service.send_message(
                msg_type="event",
                event_detail=f"{player} left the game"
            )
            server.logger.info(f"[{config.plugin_id}] 玩家离开事件已发送: {player}")
        except Exception as e:
            server.logger.error(f"[{config.plugin_id}] 发送玩家离开事件失败: {e}")

_ws_service = None

def on_load(server: PluginServerInterface, old):
    global _ws_service
    config = server.load_config_simple(target_class=GRUniChatConfig)
    server.logger.info(f'[{config.plugin_id}] GRUniChatMCDR 插件已加载，尝试建立WebSocket连接')
    _ws_service = start_ws_service(server, config)
    register_grunichat_command(server, _ws_service, config=None)
    
    # 注册事件监听器
    server.register_event_listener('info', on_info)
    server.register_event_listener('player_joined', on_player_joined)
    server.register_event_listener('player_left', on_player_left)
    
    server.logger.info(f'[{config.plugin_id}] 事件监听器已注册')

def on_server_startup(server: PluginServerInterface):
    global _ws_service
    config = server.load_config_simple(target_class=GRUniChatConfig)
    server.logger.info(f'[{config.plugin_id}] GRUniChatMCDR 服务器已启动')
    # 向 WebSocket 发送服务器已启动通知
    if _ws_service and _ws_service.ws and _ws_service.ws.sock and _ws_service.ws.sock.connected:
        try:
            _ws_service.send_message(
                msg_type="event",
                event_detail="MCDR 服务器已启动"
            )
        except Exception as e:
            server.logger.error(f"[{config.plugin_id}] WebSocket发送服务器启动通知失败: {e}")

def on_unload(server: PluginServerInterface):
    global _ws_service
    config = server.load_config_simple(target_class=GRUniChatConfig)
    # 向 WebSocket 发送插件卸载通知
    if _ws_service and _ws_service.ws and _ws_service.ws.sock and _ws_service.ws.sock.connected:
        try:
            _ws_service.send_message(
                msg_type="event",
                event_detail="GRUniChatMCDR 插件被卸载"
            )
        except Exception as e:
            server.logger.error(f"[{config.plugin_id}] WebSocket发送插件卸载通知失败: {e}")
    stop_ws_service()
