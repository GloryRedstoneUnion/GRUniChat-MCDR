from mcdreforged.api.utils.serializer import Serializable

class GRUniChatConfig(Serializable):
    ws_url: str = 'ws://127.0.0.1:8765/ws'  # WebSocket服务端地址
    plugin_id: str = 'minecraft'                     # 插件唯一标识
    forward_mc_to_ws: bool = True           # 是否转发MC消息到WebSocket
    forward_ws_to_mc: bool = True           # 是否转发WebSocket消息到MC
    # 可扩展更多配置项，如消息过滤、平台映射等
