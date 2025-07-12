import websocket
import threading
import json
import os
import time
import uuid

class WebSocketService:
    def __init__(self, server, config):
        self.server = server
        self.config = config
        self.ws = None
        self.thread = None
        self.running = False

    def _create_message(self, msg_type, sender="", chat_message="", command="", event_detail=""):
        """创建标准格式的WebSocket消息"""
        return {
            "from": self.config.plugin_id,
            "type": msg_type,
            "body": {
                "sender": sender,
                "chatMessage": chat_message,
                "command": command,
                "eventDetail": event_detail
            },
            "totalId": str(uuid.uuid4()),
            "currentTime": str(int(time.time() * 1000))
        }

    def send_message(self, msg_type, sender="", chat_message="", command="", event_detail=""):
        """发送标准格式的WebSocket消息"""
        if self.ws and self.ws.sock and self.ws.sock.connected:
            try:
                msg = self._create_message(msg_type, sender, chat_message, command, event_detail)
                self.ws.send(json.dumps(msg))
                self.server.logger.info(f"WebSocket发送消息: {msg}")
                return True
            except Exception as e:
                self.server.logger.error(f"WebSocket发送消息失败: {e}")
                return False
        else:
            self.server.logger.warning("WebSocket未连接，消息未发送")
            return False

    def on_message(self, _, message):
        try:
            if not isinstance(message, str) or not message.strip():
                return  # 忽略空消息或非字符串消息
            data = json.loads(message)
            # 适配新协议格式
            from_source = data.get('from', '')
            msg_type = data.get('type', '')
            body = data.get('body', {})
            total_id = data.get('totalId', '')
            current_time = data.get('currentTime', '')
            
            # 聊天消息
            if msg_type == 'chat' and body.get('chatMessage'):
                sender = body.get('sender', '未知')
                chat_msg = body['chatMessage']
                self.server.logger.info(f"准备say: <{sender}> {chat_msg}")
                self.server.say(f"<{sender}> {chat_msg}")
            # 指令消息
            elif msg_type == 'command' and body.get('command'):
                command = body['command']
                self.server.logger.info(f"收到WebSocket指令: {command}")
                if command.startswith('!!'):
                    self.server.execute_command(command)
                elif command.startswith('/'):
                    self.server.execute(command[1:])
                else:
                    self.server.execute_command(command)
                self.server.logger.info(f"处理WebSocket指令: {command}")
            # 事件消息
            elif msg_type == 'event' and body.get('eventDetail'):
                event_detail = body['eventDetail']
                self.server.logger.info(f"收到事件: {event_detail}")
            # 其它类型可扩展
        except Exception as e:
            self.server.logger.error(f"WebSocket消息处理异常: {e}")

    def on_error(self, wsapp, error):
        self.server.logger.error(f"WebSocket错误: {error}")

    def on_close(self, wsapp, close_status_code, close_msg):
        self.server.logger.info(f"WebSocket连接关闭 code={close_status_code}, msg={close_msg}")

    def on_open(self, wsapp):
        self.server.logger.info("WebSocket连接已建立")
        hello_msg = json.dumps({
            "from": self.config.plugin_id,
            "type": "hello",
            "body": {
                "sender": self.config.plugin_id,
                "chatMessage": "",
                "command": "",
                "eventDetail": f"Plugin {self.config.plugin_id} connected"
            },
            "totalId": str(uuid.uuid4()),
            "currentTime": str(int(time.time() * 1000))
        })
        wsapp.send(hello_msg)

    def start(self):
        self.running = True
        def run():
            try:
                self.server.logger.info(f'尝试连接WebSocket: {self.config.ws_url}')
                self.ws = websocket.WebSocketApp(
                    self.config.ws_url,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close,
                    on_open=self.on_open
                )
                self.ws.server = self.server
                self.ws.run_forever()
            except Exception as e:
                self.server.logger.error(f"WebSocket线程异常: {e}")
        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.ws:
            try:
                self.ws.close()
            except Exception as e:
                self.server.logger.error(f"WebSocket关闭异常: {e}")
            self.ws = None

    def reconnect(self, src=None):
        self.server.logger.info("WebSocket正在重连...")
        self.stop()
        self.start()
        if src:
            src.reply("§a[GRUniChat] 正在断开并重新连接...")

    def disconnect(self, src=None):
        self.stop()
        if src:
            src.reply("§a[GRUniChat] 已断开WebSocket连接")

    def connect(self, src, url):
        self.stop()
        self.config.ws_url = url
        self.start()
        src.reply(f"§a[GRUniChat] 正在连接到: {url}")

    def rename(self, src, new_id):
        self.config.plugin_id = new_id
        self.stop()
        self.start()
        # 使用 MCDR 官方方法保存配置
        if hasattr(self.config, 'save') and callable(self.config.save):
            self.config.save()
            self.server.logger.info(f"插件ID已写入配置文件: {new_id}")
        else:
            self.server.logger.warning("配置对象不支持 save()，未写入配置文件")
        src.reply(f"§a[GRUniChat] 插件ID已修改为: {new_id}")
