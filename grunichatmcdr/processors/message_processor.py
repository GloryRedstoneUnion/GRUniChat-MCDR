"""
消息处理模块
负责处理不同类型的消息格式化和发送
"""
from mcdreforged.api.all import *
from grunichatmcdr.config import GRUniChatConfig
from grunichatmcdr.core.websocket_service import WebSocketService
from typing import Optional, Dict, Any
import time


class MessageProcessor:
    """消息处理器"""
    
    def __init__(self, config: GRUniChatConfig, logger):
        self.config = config
        self.logger = logger
    
    def format_chat_message(self, sender: str, content: str) -> Dict[str, Any]:
        """格式化聊天消息"""
        return {
            "msg_type": "chat",
            "sender": sender,
            "chat_message": f"[{self.config.plugin_id}] {content}",
            "timestamp": int(time.time())
        }
    
    def format_event_message(self, event_detail: str) -> Dict[str, Any]:
        """格式化事件消息"""
        return {
            "msg_type": "event",
            "event_detail": f"[{self.config.plugin_id}] {event_detail}",
            "timestamp": int(time.time())
        }
    
    def format_command_message(self, player: str, command: str, result: str) -> Dict[str, Any]:
        """格式化命令消息"""
        return {
            "msg_type": "event",
            "event_detail": f"[{self.config.plugin_id}] Player {player} executed: {command} -> {result}",
            "timestamp": int(time.time())
        }


class MessageSender:
    """消息发送器"""
    
    def __init__(self, ws_service: Optional[WebSocketService], processor: MessageProcessor, logger):
        self.ws_service = ws_service
        self.processor = processor
        self.logger = logger
    
    def update_ws_service(self, ws_service: Optional[WebSocketService]):
        """更新WebSocket服务实例"""
        self.ws_service = ws_service
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        if not self.ws_service:
            self.logger.debug("WebSocket服务未初始化")
            return False
        
        if not self.ws_service.ws:
            self.logger.debug("WebSocket连接对象不存在")
            return False
        
        # 使用WebSocket服务自身的连接检查方法
        try:
            return (self.ws_service.ws.sock and 
                    self.ws_service.ws.sock.connected)
        except Exception as e:
            self.logger.debug(f"检查WebSocket连接状态时出错: {e}")
            return False
    
    def send_chat_message(self, sender: str, content: str) -> bool:
        """发送聊天消息"""
        self.logger.info(f"尝试发送聊天消息: {sender}: {content}")
        
        if not self.is_connected():
            self.logger.info("WebSocket未连接，跳过聊天消息发送")
            return False
        
        try:
            self.ws_service.send_message(
                msg_type="chat",
                sender=sender,
                chat_message=content
            )
            self.logger.info(f"聊天消息已发送: {sender}: {content}")
            return True
        except Exception as e:
            self.logger.error(f"发送聊天消息失败: {e}")
            return False
    
    def send_event_message(self, event_detail: str) -> bool:
        """发送事件消息"""
        self.logger.info(f"尝试发送事件消息: {event_detail}")
        
        if not self.is_connected():
            self.logger.info("WebSocket未连接，跳过事件消息发送")
            return False
        
        try:
            self.ws_service.send_message(
                msg_type="event",
                event_detail=event_detail
            )
            self.logger.info(f"事件消息已发送: {event_detail}")
            return True
        except Exception as e:
            self.logger.error(f"发送事件消息失败: {e}")
            return False
    
    def send_command_result(self, player: str, command: str, result: str) -> bool:
        """发送命令结果"""
        event_detail = f"Player {player} executed command: {command} -> {result}"
        return self.send_event_message(event_detail)
