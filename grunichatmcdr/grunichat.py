# -*- coding: utf-8 -*-
from mcdreforged.api.all import *
from mcdreforged.api.command import SimpleCommandBuilder, GreedyText
import websocket
import threading
import json
import uuid
import os

PLUGIN_METADATA = {
    'id': 'grunichat',
    'version': '0.0.1',
    'name': 'Command Executor',
    'description': '通过WebSocket接收指令并执行',
    'author': 'caikun233',
}

WS_URL = 'ws://127.0.0.1:8765/ws'  # Go中间件WebSocket服务端地址

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'mcdreforged', 'grunichat.json')
PLUGIN_CONFIG_KEY = 'plugin_id'

def load_plugin_id():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                conf = json.load(f)
                pid = conf.get(PLUGIN_CONFIG_KEY)
                if pid:
                    return pid
        except Exception:
            pass
    # 若无则生成新ID并保存
    pid = str(uuid.uuid4())
    save_plugin_id(pid)
    return pid

def save_plugin_id(pid):
    conf = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                conf = json.load(f)
        except Exception:
            conf = {}
    conf[PLUGIN_CONFIG_KEY] = pid
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(conf, f, ensure_ascii=False, indent=2)

ws = None
PLUGIN_ID = load_plugin_id()
current_ws_url = WS_URL

def on_message(wsapp, message):
    try:
        data = json.loads(message)
        if data.get('type') == 'command' and data.get('body', {}).get('command'):
            command = data['body']['command']
            wsapp.server.logger.info(f"收到WebSocket指令: {command}")
            wsapp.server.execute_command(command)
        elif data.get('type') == 'chat':
            # 优先显示 player 字段
            player = data.get('player')
            content = data.get('content')
            if player:
                wsapp.server.say(f'[WS]<{player}>: {content}')
            else:
                wsapp.server.say(f'[WS]{content}')
    except Exception as e:
        wsapp.server.logger.error(f"WebSocket消息处理异常: {e}")

def on_error(wsapp, error):
    wsapp.server.logger.error(f"WebSocket错误: {error}")

def on_close(wsapp, close_status_code, close_msg):
    wsapp.server.logger.info("WebSocket连接关闭")

def on_open(wsapp):
    wsapp.server.logger.info("WebSocket连接已建立")
    # 连接建立时发送插件ID
    hello_msg = json.dumps({
        "type": "hello",
        "plugin_id": PLUGIN_ID
    })
    wsapp.send(hello_msg)

def start_ws(server):
    def run():
        server.logger.info('尝试建立WebSocket连接...')
        global ws
        ws = websocket.WebSocketApp(
            WS_URL,
            on_message=lambda wsapp, msg: on_message(wsapp, msg),
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )
        ws.server = server
        ws.run_forever()
    threading.Thread(target=run, daemon=True).start()

def connect_ws(server, url=None):
    global ws, current_ws_url, PLUGIN_ID
    if ws:
        ws.close()
        ws = None
    if url:
        current_ws_url = url
    def run():
        server.logger.info(f'尝试连接WebSocket: {current_ws_url}')
        global ws
        ws = websocket.WebSocketApp(
            current_ws_url,
            on_message=lambda wsapp, msg: on_message(wsapp, msg),
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )
        ws.server = server
        ws.run_forever()
    threading.Thread(target=run, daemon=True).start()

def _grunichat_rename(src, new_id):
    global PLUGIN_ID
    PLUGIN_ID = new_id
    save_plugin_id(PLUGIN_ID)
    src.reply(f'§a[GRUniChat] 插件ID已修改为: {PLUGIN_ID}')
    # 重新发送hello
    if ws:
        hello_msg = json.dumps({"type": "hello", "plugin_id": PLUGIN_ID})
        try:
            ws.send(hello_msg)
        except Exception:
            src.reply('§c[GRUniChat] 发送hello消息失败，可能未连接')

def _grunichat_reconnect(src):
    src.reply('§a[GRUniChat] 正在断开并重新连接...')
    connect_ws(src.get_server())

def _grunichat_disconnect(src):
    if ws:
        ws.close()
        src.reply('§a[GRUniChat] 已断开WebSocket连接')
    else:
        src.reply('§e[GRUniChat] 当前未连接')

def _grunichat_connect(src, url):
    connect_ws(src.get_server(), url)
    src.reply(f'§a[GRUniChat] 正在连接到: {url}')

def on_info(server: PluginServerInterface, info):
    global ws
    if info.is_player and ws:
        msg = {
            "type": "chat",
            "content": f"<{info.player}> {info.content}"
        }
        try:
            ws.send(json.dumps(msg))
        except Exception as e:
            server.logger.error(f"WebSocket转发消息失败: {e}")

def on_load(server: PluginServerInterface, old_module):
    global PLUGIN_ID
    server.logger.info('GRUniChat 插件已加载')
    connect_ws(server)
    server.register_info_listener(on_info)
    builder = SimpleCommandBuilder()
    builder.command('!!grunichat rename <new_id>', lambda src, ctx: _grunichat_rename(src, ctx['new_id']))
    builder.command('!!grunichat reconnect', lambda src, ctx: _grunichat_reconnect(src))
    builder.command('!!grunichat disconnect', lambda src, ctx: _grunichat_disconnect(src))
    builder.command('!!grunichat connect <url>', lambda src, ctx: _grunichat_connect(src, ctx['url']))
    builder.command('!!grunichat', lambda src, ctx: src.reply('§a[GRUniChat] 用法: !!grunichat <rename|reconnect|disconnect|connect> [参数]'))
    builder.arg('new_id', GreedyText)
    builder.arg('url', GreedyText)
    builder.register(server)

def on_unload(server: PluginServerInterface):
    global ws
    if ws:
        server.logger.info('GRUniChat 插件正在关闭WebSocket连接...')
        try:
            ws.close()
        except Exception:
            pass
        ws = None
