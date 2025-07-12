from mcdreforged.api.all import *
from grunichatmcdr.state.plugin_state import plugin_state
import json


def register_grunichat_command(server, ws_service, config):
    # !!grunichat rename <new_id>
    rename_branch = Literal('rename').then(Text('new_id').runs(lambda src, ctx: ws_service.rename(src, ctx['new_id'], server)))
    
    # !!grunichat reconnect
    reconnect_branch = Literal('reconnect').runs(lambda src, ctx: ws_service.reconnect(src))
    
    # !!grunichat disconnect
    disconnect_branch = Literal('disconnect').runs(lambda src, ctx: ws_service.disconnect(src))
    
    # !!grunichat connect <url>
    connect_branch = Literal('connect').then(Text('url').runs(lambda src, ctx: ws_service.connect(src, ctx['url'])))
    
    # !!grunichat status - 查看插件状态
    status_branch = Literal('status').runs(lambda src, ctx: show_status(src))
    
    # !!grunichat stats - 查看详细统计
    stats_branch = Literal('stats').runs(lambda src, ctx: show_stats(src))
    
    # !!grunichat reload - 重载配置（如果可用）
    reload_branch = Literal('reload').runs(lambda src, ctx: reload_config(src, server))
    
    # !!grunichat test <message> - 测试发送消息
    test_branch = Literal('test').then(Text('message').runs(lambda src, ctx: test_send_message(src, ctx['message'])))

    tree = (
        Literal('!!grunichat')
        .runs(lambda src, ctx: show_help(src))
        .then(rename_branch)
        .then(reconnect_branch)
        .then(disconnect_branch)
        .then(connect_branch)
        .then(status_branch)
        .then(stats_branch)
        .then(reload_branch)
        .then(test_branch)
    )
    server.register_command(tree)


def show_help(src):
    """显示帮助信息"""
    help_msg = [
        '§a=== GRUniChat MCDR 插件命令 ===',
        '§7!!grunichat status §f- 查看插件状态',
        '§7!!grunichat stats §f- 查看详细统计信息',
        '§7!!grunichat rename <new_id> §f- 重命名客户端ID',
        '§7!!grunichat reconnect §f- 重新连接WebSocket',
        '§7!!grunichat disconnect §f- 断开WebSocket连接',
        '§7!!grunichat connect <url> §f- 连接到指定WebSocket服务器',
        '§7!!grunichat reload §f- 重载插件配置',
        '§7!!grunichat test <message> §f- 测试发送消息',
        '§a============================='
    ]
    for line in help_msg:
        src.reply(line)


def show_status(src):
    """显示插件状态"""
    try:
        status = plugin_state.get_status_summary()
        src.reply(f'§a[GRUniChat] {status}')
    except Exception as e:
        src.reply(f'§c[GRUniChat] 获取状态失败: {e}')


def show_stats(src):
    """显示详细统计信息"""
    try:
        stats = plugin_state.get_stats()
        config = plugin_state.get_config()
        
        stats_msg = [
            '§a=== GRUniChat 详细统计 ===',
            f'§7插件ID: §f{config.plugin_id if config else "未知"}',
            f'§7加载状态: §{"a已加载" if stats.get("is_loaded") else "c未加载"}',
            f'§7WebSocket: §{"a已连接" if stats.get("is_ws_connected") else "c未连接"}',
            f'§7运行时间: §f{stats.get("uptime", 0):.1f}秒',
            f'§7发送消息: §f{stats.get("messages_sent", 0)}条',
            f'§7失败消息: §f{stats.get("messages_failed", 0)}条',
            f'§7处理事件: §f{stats.get("events_processed", 0)}个',
            '§a========================'
        ]
        
        for line in stats_msg:
            src.reply(line)
            
    except Exception as e:
        src.reply(f'§c[GRUniChat] 获取统计信息失败: {e}')


def reload_config(src, server):
    """重载配置"""
    try:
        # 这里可以实现配置重载逻辑
        src.reply('§e[GRUniChat] 配置重载功能暂未实现')
    except Exception as e:
        src.reply(f'§c[GRUniChat] 重载配置失败: {e}')


def test_send_message(src, message):
    """测试发送消息"""
    try:
        ws_service = plugin_state.get_ws_service()
        if not ws_service:
            src.reply('§c[GRUniChat] WebSocket服务未初始化')
            return
        
        # 测试发送事件消息
        result = ws_service.send_message(
            msg_type="event",
            event_detail=f"测试消息: {message}"
        )
        
        if result:
            src.reply(f'§a[GRUniChat] 测试消息发送成功: {message}')
        else:
            src.reply(f'§c[GRUniChat] 测试消息发送失败: {message}')
            
    except Exception as e:
        src.reply(f'§c[GRUniChat] 测试发送消息出错: {e}')
