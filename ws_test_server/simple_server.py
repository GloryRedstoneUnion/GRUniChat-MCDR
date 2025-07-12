import asyncio
import websockets
import json
import time
import uuid

# WebSocket 测试服务器配置
HOST = 'localhost'
PORT = 8765

connected = set()

def create_standard_message(msg_type, sender="", chat_message="", command="", event_detail=""):
    """创建标准格式的WebSocket消息"""
    return {
        "from": "test_server",
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

async def handler(websocket):
    connected.add(websocket)
    print(f"客户端已连接: {websocket.remote_address}")
    try:
        while True:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                print(f"收到消息: {message}")
                # 解析接收到的消息并按新格式回复
                try:
                    data = json.loads(message)
                    msg_type = data.get('type', 'unknown')
                    from_source = data.get('from', 'unknown')
                    body = data.get('body', {})
                    
                    print(f"消息类型: {msg_type}, 来源: {from_source}")
                    if body:
                        print(f"消息体: {body}")
                    
                    # 发送标准格式的确认回复
                    response = create_standard_message(
                        msg_type="response",
                        event_detail=f"Received {msg_type} message from {from_source}"
                    )
                    await websocket.send(json.dumps(response))
                except Exception as e:
                    print(f"解析消息失败: {e}")
                    error_response = create_standard_message(
                        msg_type="error",
                        event_detail=f"Failed to parse message: {str(e)}"
                    )
                    await websocket.send(json.dumps(error_response))
            except asyncio.TimeoutError:
                continue
    except websockets.ConnectionClosed:
        print(f"客户端断开: {websocket.remote_address}")
    finally:
        connected.remove(websocket)

async def send_message_to_all(msg_dict):
    if connected:
        message = json.dumps(msg_dict)
        # websockets 10.x+ ServerConnection 没有 open 属性，直接尝试发送，捕获异常即可
        for ws in list(connected):
            try:
                await ws.send(message)
            except Exception as e:
                print(f"发送到客户端失败: {e}")
        print(f"已向所有客户端发送: {message}")
    else:
        print("没有客户端连接，无法发送消息")

async def send_test_messages():
    """发送一些测试消息的示例"""
    # 测试聊天消息
    chat_msg = create_standard_message(
        msg_type="chat",
        sender="TestUser",
        chat_message="这是一条测试聊天消息"
    )
    await send_message_to_all(chat_msg)
    
    # 测试命令消息
    cmd_msg = create_standard_message(
        msg_type="command",
        command="!!server status"
    )
    await send_message_to_all(cmd_msg)
    
    # 测试事件消息
    event_msg = create_standard_message(
        msg_type="event",
        event_detail="测试服务器发送的事件消息"
    )
    await send_message_to_all(event_msg)

async def main():
    server = await websockets.serve(handler, HOST, PORT)
    print(f"WebSocket 测试服务器已启动: ws://{HOST}:{PORT}")
    print("可用命令:")
    print("  'test' - 发送测试消息")
    print("  'exit' - 退出服务器")
    print("  或输入符合新协议格式的JSON消息")
    
    # 控制台输入测试
    loop = asyncio.get_event_loop()
    while True:
        try:
            raw = await loop.run_in_executor(None, input, "输入命令或JSON消息：\n")
            if raw.strip().lower() == 'exit':
                break
            elif raw.strip().lower() == 'test':
                await send_test_messages()
            else:
                msg_dict = json.loads(raw)
                await send_message_to_all(msg_dict)
        except Exception as e:
            print(f"输入或发送消息出错: {e}")
    server.close()
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
