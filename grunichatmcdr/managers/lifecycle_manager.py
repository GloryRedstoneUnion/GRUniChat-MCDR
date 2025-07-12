"""
插件生命周期管理模块
负责管理插件的加载、卸载和状态管理
"""
from mcdreforged.api.all import *
from grunichatmcdr.config import GRUniChatConfig
from grunichatmcdr.core.main import start_ws_service, stop_ws_service
from grunichatmcdr.cmd.command_tree import register_grunichat_command
from grunichatmcdr.handlers.event_handler import EventHandler
from grunichatmcdr.state.plugin_state import plugin_state
from typing import Optional


class PluginLifecycleManager:
    """插件生命周期管理器"""
    
    def __init__(self):
        self.event_handler: Optional[EventHandler] = None
    
    def load(self, server: PluginServerInterface, old=None):
        """加载插件"""
        try:
            # 加载配置
            config = server.load_config_simple(target_class=GRUniChatConfig)
            
            server.logger.info(f'[{config.plugin_id}] GRUniChatMCDR 插件开始加载...')
            
            # 更新状态
            plugin_state.set_server(server)
            plugin_state.set_config(config)
            
            # 启动WebSocket服务
            ws_service = start_ws_service(server, config)
            plugin_state.set_ws_service(ws_service)
            
            # 初始化事件处理器
            self.event_handler = EventHandler(server, ws_service, config)
            
            # 注册命令
            register_grunichat_command(server, ws_service, config=None)
            
            # 注册事件监听器
            self._register_event_listeners(server)
            
            # 设置加载状态
            plugin_state.set_loaded(True)
            
            server.logger.info(f'[{config.plugin_id}] GRUniChatMCDR 插件加载完成')
            server.logger.info(f'[{config.plugin_id}] {plugin_state.get_status_summary()}')
            
        except Exception as e:
            plugin_state.set_loaded(False)
            server.logger.error(f'插件加载失败: {e}')
            raise
    
    def unload(self, server: PluginServerInterface):
        """卸载插件"""
        try:
            config = plugin_state.get_config()
            plugin_id = config.plugin_id if config else "GRUniChat"
            
            # 发送卸载事件
            if self.event_handler:
                self.event_handler.handle_plugin_unload()
            
            # 停止WebSocket服务
            stop_ws_service()
            
            # 更新状态
            plugin_state.set_loaded(False)
            plugin_state.set_ws_service(None)
            
            server.logger.info(f'[{plugin_id}] 插件已卸载')
            
        except Exception as e:
            server.logger.error(f'插件卸载时发生错误: {e}')
    
    def on_server_startup(self, server: PluginServerInterface):
        """服务器启动回调"""
        if self.event_handler:
            self.event_handler.handle_server_startup()
    
    def get_event_handler(self) -> Optional[EventHandler]:
        """获取事件处理器"""
        return self.event_handler
    
    def update_ws_service(self, ws_service):
        """更新WebSocket服务"""
        plugin_state.set_ws_service(ws_service)
        if self.event_handler:
            self.event_handler.update_ws_service(ws_service)
    
    def get_status(self) -> str:
        """获取插件状态"""
        return plugin_state.get_status_summary()
    
    def get_stats(self) -> dict:
        """获取插件统计信息"""
        return plugin_state.get_stats()
    
    def _register_event_listeners(self, server: PluginServerInterface):
        """注册事件监听器"""
        if not self.event_handler:
            return
        
        # 注册事件监听器
        server.register_event_listener('info', self._on_info)
        server.register_event_listener('player_joined', self._on_player_joined)
        server.register_event_listener('player_left', self._on_player_left)
        
        config = plugin_state.get_config()
        plugin_id = config.plugin_id if config else "GRUniChat"
        server.logger.info(f'[{plugin_id}] 事件监听器已注册')
    
    def _on_info(self, server: PluginServerInterface, info: Info):
        """info事件回调"""
        if self.event_handler:
            self.event_handler.handle_info(info)
    
    def _on_player_joined(self, server: PluginServerInterface, player: str, info: Info):
        """玩家加入事件回调"""
        if self.event_handler:
            self.event_handler.handle_player_joined(player, info)
    
    def _on_player_left(self, server: PluginServerInterface, player: str):
        """玩家离开事件回调"""
        if self.event_handler:
            self.event_handler.handle_player_left(player)
