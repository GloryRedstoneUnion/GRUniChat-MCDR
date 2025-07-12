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

    def _strip_prefix(self, text, prefix_source):
        """去掉消息内容中的前缀"""
        if text and prefix_source:
            prefix = f"[{prefix_source}] "
            if text.startswith(prefix):
                return text[len(prefix):]
        return text

    def _create_message(self, msg_type, sender="", chat_message="", command="", event_detail=""):
        """创建标准格式的WebSocket消息"""
        # 只为非chat消息的内容添加plugin_id前缀
        if msg_type != 'chat':
            if command:
                command = f"[{self.config.plugin_id}] {command}"
            if event_detail:
                event_detail = f"[{self.config.plugin_id}] {event_detail}"
            if sender:
                sender = f"[{self.config.plugin_id}] {sender}"
            
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
                
                # 调试级别的详细日志
                self.server.logger.debug(f"[{self.config.plugin_id}] WebSocket发送消息: {msg}")
                
                # 简化的INFO级别日志
                if msg_type == 'chat':
                    self.server.logger.info(f"[{self.config.plugin_id}] WebSocket转发聊天: <{sender}> {chat_message}")
                elif msg_type == 'event':
                    self.server.logger.info(f"[{self.config.plugin_id}] WebSocket转发事件: {event_detail}")
                elif msg_type == 'command':
                    self.server.logger.info(f"[{self.config.plugin_id}] WebSocket转发命令: {command}")
                # 对于其他消息类型（如hello），不输出INFO级别日志
                
                return True
            except Exception as e:
                self.server.logger.error(f"[{self.config.plugin_id}] WebSocket发送消息失败: {e}")
                return False
        else:
            self.server.logger.debug(f"[{self.config.plugin_id}] WebSocket未连接，消息未发送")
            return False

    def on_message(self, _, message):
        try:
            if not isinstance(message, str) or not message.strip():
                return  # 忽略空消息或非字符串消息
            
            # 调试级别的详细日志
            self.server.logger.debug(f"[{self.config.plugin_id}] 收到WebSocket原始消息: {message}")
            
            data = json.loads(message)
            self.server.logger.debug(f"[{self.config.plugin_id}] 解析后的消息数据: {data}")
            
            # 适配新协议格式
            from_source = data.get('from', '')
            msg_type = data.get('type', '')
            body = data.get('body', {})
            total_id = data.get('totalId', '')
            current_time = data.get('currentTime', '')
            
            self.server.logger.debug(f"[{self.config.plugin_id}] 消息来源: {from_source}, 类型: {msg_type}, 本插件ID: {self.config.plugin_id}")
            
            # 处理确认消息（ack）
            if msg_type == 'ack':
                status = data.get('status', '')
                message_text = data.get('message', '')
                timestamp = data.get('timestamp', '')
                total_id = data.get('totalId', '')
                
                if status == 'success':
                    # 成功时静默处理，不输出日志
                    pass
                else:
                    # 失败时输出错误日志
                    self.server.logger.error(f"[{self.config.plugin_id}] WebSocket消息确认失败 [ID: {total_id}]: {message_text}")
                return  # 处理完确认消息后直接返回
            
            # 处理错误消息（error）
            elif msg_type == 'error':
                error_msg = data.get('error', '')
                error_code = data.get('code', 0)
                timestamp = data.get('timestamp', '')
                total_id = data.get('totalId', '')
                
                self.server.logger.error(f"[{self.config.plugin_id}] WebSocket错误 [ID: {total_id}, Code: {error_code}]: {error_msg}")
                return  # 处理完错误消息后直接返回
            
            # 聊天消息
            elif msg_type == 'chat' and body.get('chatMessage'):
                sender = body.get('sender', '未知')
                chat_msg = body['chatMessage']
                self.server.logger.info(f"[{self.config.plugin_id}] 准备say: <{sender}> {chat_msg}")
                try:
                    # 在转发到Minecraft时，在sender前面加上消息来源的plugin_id前缀
                    display_sender = f"[{from_source}] {sender}" if from_source else sender
                    self.server.say(f"<{display_sender}> {chat_msg}")
                    self.server.logger.info(f"[{self.config.plugin_id}] 已执行say: <{display_sender}> {chat_msg}")
                except Exception as say_e:
                    self.server.logger.error(f"[{self.config.plugin_id}] 执行say失败: {say_e}")
            # 指令消息
            elif msg_type == 'command' and body.get('command'):
                command = body['command']
                self.server.logger.info(f"[{self.config.plugin_id}] 收到WebSocket指令: {command}")
                # 去掉来源前缀，得到实际的命令
                actual_command = self._strip_prefix(command, from_source)
                
                if actual_command.startswith('!!'):
                    self.server.execute_command(actual_command)
                elif actual_command.startswith('/'):
                    self.server.execute(actual_command[1:])
                else:
                    self.server.execute_command(actual_command)
                self.server.logger.info(f"[{self.config.plugin_id}] 处理WebSocket指令: {actual_command}")
            # 事件消息
            elif msg_type == 'event' and body.get('eventDetail'):
                event_detail = body['eventDetail']
                self.server.logger.info(f"[{self.config.plugin_id}] 收到事件: {event_detail}")
            # 其它类型可扩展
        except Exception as e:
            self.server.logger.error(f"[{self.config.plugin_id}] WebSocket消息处理异常: {e}")

    def on_error(self, wsapp, error):
        self.server.logger.error(f"[{self.config.plugin_id}] WebSocket错误: {error}")

    def on_close(self, wsapp, close_status_code, close_msg):
        self.server.logger.info(f"[{self.config.plugin_id}] WebSocket连接关闭 code={close_status_code}, msg={close_msg}")

    def on_open(self, wsapp):
        self.server.logger.info(f"[{self.config.plugin_id}] WebSocket连接已建立")
        hello_msg = json.dumps({
            "from": self.config.plugin_id,
            "type": "hello",
            "body": {
                "sender": self.config.plugin_id,
                "chatMessage": "",
                "command": "",
                "eventDetail": f"[{self.config.plugin_id}] Plugin {self.config.plugin_id} connected"
            },
            "totalId": str(uuid.uuid4()),
            "currentTime": str(int(time.time() * 1000))
        })
        wsapp.send(hello_msg)

    def start(self):
        self.running = True
        def run():
            try:
                self.server.logger.debug(f'[{self.config.plugin_id}] 尝试连接WebSocket: {self.config.ws_url}')
                self.server.logger.debug(f'[{self.config.plugin_id}] 配置对象类型: {type(self.config)}')
                self.server.logger.debug(f'[{self.config.plugin_id}] 配置ws_url属性: {getattr(self.config, "ws_url", "属性不存在")}')
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
                self.server.logger.error(f"[{self.config.plugin_id}] WebSocket线程异常: {e}")
        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.ws:
            try:
                self.ws.close()
            except Exception as e:
                self.server.logger.error(f"[{self.config.plugin_id}] WebSocket关闭异常: {e}")
            self.ws = None

    def reconnect(self, src=None):
        self.server.logger.info(f"[{self.config.plugin_id}] WebSocket正在重连...")
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

    def rename(self, src, new_id, server=None):
        old_id = self.config.plugin_id
        self.config.plugin_id = new_id
        self.stop()
        self.start()
        
        # 使用传入的server或使用实例的server来保存配置
        save_server = server if server else self.server
        try:
            save_server.save_config_simple(self.config)
            self.server.logger.info(f"[{new_id}] 插件ID已写入配置文件: {old_id} -> {new_id}")
        except Exception as e:
            self.server.logger.error(f"[{new_id}] 保存配置文件失败: {e}")
            
        src.reply(f"§a[GRUniChat] 插件ID已修改为: {new_id}")
