# MCDR GRUniChatMCDR 插件入口 - 模块化重构版本
from mcdreforged.api.all import *
from grunichatmcdr.managers.lifecycle_manager import PluginLifecycleManager
from grunichatmcdr.state.plugin_state import plugin_state

# 全局生命周期管理器实例
lifecycle_manager = PluginLifecycleManager()


def on_load(server: PluginServerInterface, old):
    """插件加载回调"""
    lifecycle_manager.load(server, old)


def on_unload(server: PluginServerInterface):
    """插件卸载回调"""
    lifecycle_manager.unload(server)


def on_server_startup(server: PluginServerInterface):
    """服务器启动回调"""
    lifecycle_manager.on_server_startup(server)


def on_info(server: PluginServerInterface, info: Info):
    """信息事件回调"""
    event_handler = lifecycle_manager.get_event_handler()
    if event_handler:
        event_handler.handle_info(info)


def on_player_joined(server: PluginServerInterface, player: str, info: Info):
    """玩家加入事件回调"""
    event_handler = lifecycle_manager.get_event_handler()
    if event_handler:
        event_handler.handle_player_joined(player, info)


def on_player_left(server: PluginServerInterface, player: str):
    """玩家离开事件回调"""
    event_handler = lifecycle_manager.get_event_handler()
    if event_handler:
        event_handler.handle_player_left(player)


# 辅助函数 - 提供给其他模块或命令使用
def get_plugin_status() -> str:
    """获取插件状态摘要"""
    return lifecycle_manager.get_status()


def get_plugin_stats() -> dict:
    """获取插件统计信息"""
    return lifecycle_manager.get_stats()


def is_plugin_loaded() -> bool:
    """检查插件是否已加载"""
    return plugin_state.is_loaded()


def is_websocket_connected() -> bool:
    """检查WebSocket是否已连接"""
    return plugin_state.is_ws_connected()
