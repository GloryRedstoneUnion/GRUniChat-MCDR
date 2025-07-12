"""
插件状态管理模块
负责管理插件的全局状态和配置
"""
from mcdreforged.api.all import *
from grunichatmcdr.config import GRUniChatConfig
from grunichatmcdr.core.websocket_service import WebSocketService
from typing import Optional, Dict, Any
import threading
import time


class PluginState:
    """插件状态管理器"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._server: Optional[PluginServerInterface] = None
        self._config: Optional[GRUniChatConfig] = None
        self._ws_service: Optional[WebSocketService] = None
        self._is_loaded = False
        self._load_time: Optional[float] = None
        self._stats: Dict[str, Any] = {
            'messages_sent': 0,
            'messages_failed': 0,
            'events_processed': 0,
            'last_activity': None
        }
    
    def set_server(self, server: PluginServerInterface):
        """设置服务器实例"""
        with self._lock:
            self._server = server
    
    def get_server(self) -> Optional[PluginServerInterface]:
        """获取服务器实例"""
        with self._lock:
            return self._server
    
    def set_config(self, config: GRUniChatConfig):
        """设置配置"""
        with self._lock:
            self._config = config
    
    def get_config(self) -> Optional[GRUniChatConfig]:
        """获取配置"""
        with self._lock:
            return self._config
    
    def set_ws_service(self, ws_service: Optional[WebSocketService]):
        """设置WebSocket服务"""
        with self._lock:
            self._ws_service = ws_service
    
    def get_ws_service(self) -> Optional[WebSocketService]:
        """获取WebSocket服务"""
        with self._lock:
            return self._ws_service
    
    def set_loaded(self, loaded: bool):
        """设置加载状态"""
        with self._lock:
            self._is_loaded = loaded
            if loaded:
                self._load_time = time.time()
            else:
                self._load_time = None
    
    def is_loaded(self) -> bool:
        """检查是否已加载"""
        with self._lock:
            return self._is_loaded
    
    def get_load_time(self) -> Optional[float]:
        """获取加载时间"""
        with self._lock:
            return self._load_time
    
    def get_uptime(self) -> Optional[float]:
        """获取运行时间（秒）"""
        with self._lock:
            if self._load_time:
                return time.time() - self._load_time
            return None
    
    def is_ws_connected(self) -> bool:
        """检查WebSocket连接状态"""
        with self._lock:
            return (self._ws_service and 
                    self._ws_service.ws and 
                    self._ws_service.ws.sock and 
                    self._ws_service.ws.sock.connected)
    
    def increment_messages_sent(self):
        """增加发送消息计数"""
        with self._lock:
            self._stats['messages_sent'] += 1
            self._stats['last_activity'] = time.time()
    
    def increment_messages_failed(self):
        """增加失败消息计数"""
        with self._lock:
            self._stats['messages_failed'] += 1
            self._stats['last_activity'] = time.time()
    
    def increment_events_processed(self):
        """增加处理事件计数"""
        with self._lock:
            self._stats['events_processed'] += 1
            self._stats['last_activity'] = time.time()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            stats = self._stats.copy()
            stats['is_loaded'] = self._is_loaded
            stats['is_ws_connected'] = self.is_ws_connected()
            stats['uptime'] = self.get_uptime()
            return stats
    
    def reset_stats(self):
        """重置统计信息"""
        with self._lock:
            self._stats = {
                'messages_sent': 0,
                'messages_failed': 0,
                'events_processed': 0,
                'last_activity': None
            }
    
    def get_status_summary(self) -> str:
        """获取状态摘要"""
        with self._lock:
            if not self._is_loaded:
                return "插件未加载"
            
            config_id = self._config.plugin_id if self._config else "unknown"
            ws_status = "已连接" if self.is_ws_connected() else "未连接"
            uptime = self.get_uptime()
            uptime_str = f"{uptime:.1f}秒" if uptime else "未知"
            
            return (f"插件状态: 已加载 | "
                   f"ID: {config_id} | "
                   f"WebSocket: {ws_status} | "
                   f"运行时间: {uptime_str} | "
                   f"消息: {self._stats['messages_sent']}发送/{self._stats['messages_failed']}失败 | "
                   f"事件: {self._stats['events_processed']}处理")


# 全局状态实例
plugin_state = PluginState()
