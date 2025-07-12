"""
MCDR事件处理模块
负责处理各种MCDR事件的分发和处理
"""
from mcdreforged.api.all import *
from grunichatmcdr.config import GRUniChatConfig
from grunichatmcdr.core.websocket_service import WebSocketService
from grunichatmcdr.processors.message_processor import MessageProcessor, MessageSender
from grunichatmcdr.state.plugin_state import plugin_state
from typing import Optional


class EventHandler:
    """MCDR事件处理器"""
    
    def __init__(self, server: PluginServerInterface, ws_service: Optional[WebSocketService], config: GRUniChatConfig):
        self.server = server
        self.config = config
        self.logger = server.logger
        
        # 初始化消息处理器和发送器
        self.message_processor = MessageProcessor(config, self.logger)
        self.message_sender = MessageSender(ws_service, self.message_processor, self.logger)
        
        # 更新状态
        plugin_state.set_server(server)
        plugin_state.set_config(config)
        plugin_state.set_ws_service(ws_service)
    
    def update_ws_service(self, ws_service: Optional[WebSocketService]):
        """更新WebSocket服务实例"""
        self.message_sender.update_ws_service(ws_service)
        plugin_state.set_ws_service(ws_service)
    
    def handle_info(self, info: Info):
        """处理info事件"""
        try:
            plugin_state.increment_events_processed()
            
            # 聊天消息
            if info.is_player and info.player:
                self._handle_chat_message(info)
            # 玩家命令
            elif self._is_command_result(info.content):
                self._handle_command_result(info.content)
                
        except Exception as e:
            self.logger.error(f"[{self.config.plugin_id}] 处理info事件失败: {e}")
    
    def handle_player_joined(self, player: str, info: Info):
        """处理玩家加入事件"""
        try:
            plugin_state.increment_events_processed()
            
            if self.message_sender.send_event_message(f"{player} joined the game"):
                plugin_state.increment_messages_sent()
                self.logger.info(f"[{self.config.plugin_id}] 玩家加入事件已发送: {player}")
            else:
                plugin_state.increment_messages_failed()
                
        except Exception as e:
            plugin_state.increment_messages_failed()
            self.logger.error(f"[{self.config.plugin_id}] 发送玩家加入事件失败: {e}")
    
    def handle_player_left(self, player: str):
        """处理玩家离开事件"""
        try:
            plugin_state.increment_events_processed()
            
            if self.message_sender.send_event_message(f"{player} left the game"):
                plugin_state.increment_messages_sent()
                self.logger.info(f"[{self.config.plugin_id}] 玩家离开事件已发送: {player}")
            else:
                plugin_state.increment_messages_failed()
                
        except Exception as e:
            plugin_state.increment_messages_failed()
            self.logger.error(f"[{self.config.plugin_id}] 发送玩家离开事件失败: {e}")
    
    def handle_server_startup(self):
        """处理服务器启动事件"""
        try:
            plugin_state.increment_events_processed()
            
            if self.message_sender.send_event_message("MCDR 服务器已启动"):
                plugin_state.increment_messages_sent()
                self.logger.info(f"[{self.config.plugin_id}] 服务器启动事件已发送")
            else:
                plugin_state.increment_messages_failed()
                
        except Exception as e:
            plugin_state.increment_messages_failed()
            self.logger.error(f"[{self.config.plugin_id}] WebSocket发送服务器启动通知失败: {e}")
    
    def handle_plugin_unload(self):
        """处理插件卸载事件"""
        try:
            plugin_state.increment_events_processed()
            
            if self.message_sender.send_event_message("GRUniChatMCDR 插件被卸载"):
                plugin_state.increment_messages_sent()
                self.logger.info(f"[{self.config.plugin_id}] 插件卸载事件已发送")
            else:
                plugin_state.increment_messages_failed()
                
        except Exception as e:
            plugin_state.increment_messages_failed()
            self.logger.error(f"[{self.config.plugin_id}] WebSocket发送插件卸载通知失败: {e}")
    
    def _handle_chat_message(self, info: Info):
        """处理聊天消息"""
        if self.message_sender.send_chat_message(info.player, info.content):
            plugin_state.increment_messages_sent()
            self.logger.debug(f"[{self.config.plugin_id}] 聊天消息已发送: {info.player}: {info.content}")
        else:
            plugin_state.increment_messages_failed()
    
    def _is_command_result(self, content: str) -> bool:
        """检查是否是命令结果"""
        return (content.startswith("[") and 
                ":" in content and 
                content.endswith("]"))
    
    def _handle_command_result(self, content: str):
        """处理命令结果"""
        # 解析命令信息 - 格式: [玩家名: 命令结果]
        command_info = content[1:-1]  # 去掉方括号
        if ":" in command_info:
            player_part, command_result = command_info.split(":", 1)
            player_name = player_part.strip()
            command_desc = command_result.strip()
            
            if self.message_sender.send_command_result(player_name, "command", command_desc):
                plugin_state.increment_messages_sent()
                self.logger.debug(f"[{self.config.plugin_id}] 命令结果已发送: {player_name}: {command_desc}")
            else:
                plugin_state.increment_messages_failed()
