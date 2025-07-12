# WebSocket 消息协议文档

## 消息格式

所有WebSocket消息都应遵循以下标准格式：

```json
{
  "from": "消息来源标识",
  "type": "消息类型",
  "body": {
    "sender": "发送者名称",
    "chatMessage": "聊天消息内容",
    "command": "命令内容",
    "eventDetail": "事件详情"
  },
  "totalId": "唯一消息ID",
  "currentTime": "时间戳(毫秒)"
}
```

## 字段说明

- `from`: 消息来源，如 "mcdr_plugin", "web_client", "external_system" 等
- `type`: 消息类型，支持以下类型：
  - `chat`: 聊天消息
  - `command`: 命令消息
  - `event`: 事件消息
  - `hello`: 连接握手消息
  - `response`: 响应消息
  - `error`: 错误消息
- `body`: 消息主体
  - `sender`: 发送者名称（聊天消息时使用）
  - `chatMessage`: 聊天消息内容（聊天消息时使用）
  - `command`: 命令内容（命令消息时使用）
  - `eventDetail`: 事件详情（事件消息时使用）
- `totalId`: 唯一消息ID，建议使用UUID
- `currentTime`: 时间戳，毫秒格式

## 消息类型示例

### 1. 聊天消息
```json
{
  "from": "web_client",
  "type": "chat",
  "body": {
    "sender": "WebUser",
    "chatMessage": "Hello from web!",
    "command": "",
    "eventDetail": ""
  },
  "totalId": "12345678-1234-1234-1234-123456789abc",
  "currentTime": "1721634567890"
}
```

### 2. 命令消息
```json
{
  "from": "web_client",
  "type": "command",
  "body": {
    "sender": "",
    "chatMessage": "",
    "command": "!!server status",
    "eventDetail": ""
  },
  "totalId": "12345678-1234-1234-1234-123456789def",
  "currentTime": "1721634567891"
}
```

### 3. 事件消息
```json
{
  "from": "mcdr_plugin",
  "type": "event",
  "body": {
    "sender": "",
    "chatMessage": "",
    "command": "",
    "eventDetail": "Player Steve joined the game"
  },
  "totalId": "12345678-1234-1234-1234-123456789ghi",
  "currentTime": "1721634567892"
}
```

## 测试服务器使用说明

1. 启动测试服务器：
   ```bash
   cd ws_test_server
   python simple_server.py
   ```

2. 服务器支持以下命令：
   - `test`: 发送测试消息
   - `exit`: 退出服务器
   - 或直接输入符合协议格式的JSON消息

3. 示例消息可参考 `message_examples.json` 文件

## 插件发送的消息类型

- **hello**: 插件连接时发送的握手消息
- **chat**: 玩家聊天消息转发
- **event**: 游戏事件（玩家进服、退服、服务器启动等）

## 插件接收的消息类型

- **chat**: 将消息转发到游戏聊天
- **command**: 执行游戏命令
- **event**: 记录事件日志
