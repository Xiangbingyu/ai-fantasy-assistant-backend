# AI Fantasy Assistant Backend API Documentation

## 概述

本文档描述了AI Fantasy Assistant后端系统的所有API接口，包括REST API和WebSocket接口。系统主要用于管理虚拟世界、章节、对话消息，以及提供AI驱动的聊天和剧情分析功能。

## 目录

- [数据库管理API (db.py)](#数据库管理api-dbpy)
- [AI语言模型API (llm.py)](#ai语言模型api-llmpy)
- [WebSocket实时通信 (websocket.py)](#websocket实时通信-websocketpy)

---

## 数据库管理API (db.py)

### 基础信息
- **基础路径**: `/api`
- **认证**: 部分接口需要认证
- **数据格式**: JSON

### 世界管理

#### 获取所有世界
```http
GET /api/worlds
```

**响应示例**:
```json
{
  "success": true,
  "worlds": [
    {
      "id": 1,
      "name": "魔法世界",
      "description": "充满魔法与冒险的世界",
      "popularity": 100,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### 获取单个世界详情
```http
GET /api/worlds/{world_id}
```

**路径参数**:
- `world_id` (int): 世界ID

**响应示例**:
```json
{
  "success": true,
  "world": {
    "id": 1,
    "name": "魔法世界",
    "description": "充满魔法与冒险的世界",
    "popularity": 100,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### 创建新世界
```http
POST /api/worlds
```

**请求体**:
```json
{
  "name": "新世界",
  "description": "世界描述",
  "popularity": 0
}
```

#### 删除世界
```http
DELETE /api/worlds/{world_id}
```

**路径参数**:
- `world_id` (int): 世界ID

#### 增加世界人气值
```http
POST /api/worlds/{world_id}/increase-popularity
```

**路径参数**:
- `world_id` (int): 世界ID

### 章节管理

#### 获取世界的所有章节
```http
GET /api/worlds/{world_id}/chapters
```

**路径参数**:
- `world_id` (int): 世界ID

#### 获取单个章节详情
```http
GET /api/chapters/{chapter_id}
```

**路径参数**:
- `chapter_id` (int): 章节ID

#### 创建新章节
```http
POST /api/chapters
```

**请求体**:
```json
{
  "world_id": 1,
  "title": "章节标题",
  "content": "章节内容"
}
```

#### 删除章节
```http
DELETE /api/chapters/{chapter_id}
```

**路径参数**:
- `chapter_id` (int): 章节ID

### 消息管理

#### 获取章节的所有消息
```http
GET /api/chapters/{chapter_id}/messages
```

**路径参数**:
- `chapter_id` (int): 章节ID

#### 创建新消息
```http
POST /api/messages
```

**请求体**:
```json
{
  "chapter_id": 1,
  "user_id": 1,
  "role": "user",
  "content": "消息内容"
}
```

#### 删除消息
```http
DELETE /api/chapters/{chapter_id}/messages
```

**路径参数**:
- `chapter_id` (int): 章节ID

**查询参数**:
- `from_id` (int, 可选): 从指定消息ID开始删除

### 小说记录管理

#### 获取所有小说记录
```http
GET /api/novels
```

#### 获取章节的小说记录
```http
GET /api/chapters/{chapter_id}/novels
```

**路径参数**:
- `chapter_id` (int): 章节ID

#### 创建小说记录
```http
POST /api/novels
```

**请求体**:
```json
{
  "chapter_id": 1,
  "user_id": 1,
  "title": "小说标题",
  "content": "小说内容"
}
```

### 用户世界关系

#### 获取用户世界关系
```http
GET /api/user-worlds
```

#### 创建用户世界关系
```http
POST /api/user-worlds
```

**请求体**:
```json
{
  "user_id": 1,
  "world_id": 1
}
```

#### 删除用户世界关系
```http
DELETE /api/user-worlds
```

**查询参数**:
- `user_id` (int): 用户ID
- `world_id` (int): 世界ID

### 认证

#### 用户认证
```http
POST /api/auth
```

**请求体**:
```json
{
  "username": "用户名",
  "password": "密码"
}
```

---

## AI语言模型API (llm.py)

### 基础信息
- **基础路径**: `/api`
- **模型**: GLM-4-Plus
- **认证**: 无特殊认证要求

### 聊天交互

#### 智能聊天
```http
POST /api/chat
```

**请求体**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "用户消息"
    }
  ],
  "worldview": "世界观描述",
  "master_sitting": "核心人物设定",
  "main_characters": ["角色1", "角色2"],
  "background": "玩家背景",
  "story_analysis": "剧情分析",
  "story_guide": "剧情引导"
}
```

**响应示例**:
```json
{
  "success": true,
  "response": "AI回复内容"
}
```

#### 生成对话建议
```http
POST /api/chat/suggestions
```

**请求体**:
```json
{
  "messages": [
    {
      "role": "user", 
      "content": "用户消息"
    }
  ],
  "worldview": "世界观描述",
  "master_sitting": "核心人物设定",
  "main_characters": ["角色1", "角色2"],
  "background": "玩家背景",
  "story_analysis": "剧情分析"
}
```

**响应示例**:
```json
{
  "success": true,
  "suggestions": [
    "建议1",
    "建议2",
    "建议3"
  ]
}
```

#### 剧情分析
```http
POST /api/chat/analyze
```

**请求体**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "用户消息"
    }
  ],
  "worldview": "世界观描述",
  "master_sitting": "核心人物设定",
  "main_characters": ["角色1", "角色2"],
  "background": "玩家背景"
}
```

**响应示例**:
```json
{
  "success": true,
  "analysis": "剧情分析结果"
}
```

### 小说生成

#### 生成小说内容
```http
POST /api/novel
```

**请求体**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "用户消息"
    }
  ],
  "worldview": "世界观描述",
  "master_sitting": "核心人物设定",
  "main_characters": ["角色1", "角色2"],
  "background": "玩家背景",
  "story_analysis": "剧情分析",
  "story_guide": "剧情引导"
}
```

**响应示例**:
```json
{
  "success": true,
  "novel": "生成的小说内容"
}
```

---

## WebSocket实时通信 (websocket.py)

### 基础信息
- **协议**: WebSocket
- **CORS**: 允许所有来源
- **模型**: GLM-4-Plus

### 连接事件

#### 客户端连接
```javascript
socket.on('connect', function() {
  console.log('已连接到服务器');
});
```

**服务器响应**:
```json
{
  "status": "connected"
}
```

#### 客户端断开连接
```javascript
socket.on('disconnect', function() {
  console.log('已断开连接');
});
```

### 房间管理

#### 加入房间
```javascript
socket.emit('join', {
  room: 'room_name'
});
```

**服务器响应**:
```json
{
  "room": "room_name",
  "status": "joined"
}
```

### 聊天功能

#### 流式聊天
```javascript
socket.emit('chat_stream', {
  messages: [
    {
      "role": "user",
      "content": "用户消息"
    }
  ],
  worldview: "世界观描述",
  master_sitting: "核心人物设定",
  main_characters: ["角色1", "角色2"],
  background: "玩家背景",
  story_analysis: "剧情分析",
  story_guide: "剧情引导",
  chapterId: 1,
  userId: 1
});
```

**流式响应事件**:
- `chat_stream_data`: 流式数据片段
```json
{
  "content": "内容片段",
  "finished": false
}
```

- `chat_stream_end`: 流式结束
```json
{
  "finished": true,
  "message_id": 123
}
```

- `chat_stream_error`: 错误信息
```json
{
  "error": "错误描述"
}
```

#### 流式剧情分析
```javascript
socket.emit('chat_analyze_stream', {
  messages: [
    {
      "role": "user",
      "content": "用户消息"
    }
  ],
  worldview: "世界观描述",
  master_sitting: "核心人物设定",
  main_characters: ["角色1", "角色2"],
  background: "玩家背景"
});
```

**流式响应事件**:
- `chat_analyze_stream_data`: 分析数据片段
```json
{
  "content": "分析内容片段",
  "finished": false
}
```

- `chat_analyze_stream_end`: 分析完成
```json
{
  "finished": true
}
```

- `chat_analyze_stream_error`: 分析错误
```json
{
  "error": "错误描述"
}
```

---

## 错误处理

### 标准错误响应格式
```json
{
  "success": false,
  "error": "错误描述",
  "code": "ERROR_CODE"
}
```

### 常见错误码
- `404`: 资源未找到
- `400`: 请求参数错误
- `500`: 服务器内部错误
- `401`: 认证失败

---

## 使用示例

### JavaScript客户端示例

#### REST API调用
```javascript
// 获取所有世界
fetch('/api/worlds')
  .then(response => response.json())
  .then(data => console.log(data));

// 创建新世界
fetch('/api/worlds', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: '新世界',
    description: '世界描述',
    popularity: 0
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

#### WebSocket连接示例
```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:5000');

// 连接事件
socket.on('connect', () => {
  console.log('已连接');
});

// 加入房间
socket.emit('join', { room: 'room1' });

// 发送聊天消息
socket.emit('chat_stream', {
  messages: [{ role: 'user', content: '你好' }],
  worldview: '魔法世界',
  master_sitting: '法师角色',
  main_characters: ['法师', '战士'],
  background: '冒险者',
  story_analysis: '当前剧情',
  story_guide: '探索任务',
  chapterId: 1,
  userId: 1
});

// 接收流式响应
socket.on('chat_stream_data', (data) => {
  console.log('收到数据:', data.content);
});

socket.on('chat_stream_end', (data) => {
  console.log('聊天结束, 消息ID:', data.message_id);
});
```

---

## 注意事项

1. **数据格式**: 所有API请求和响应均使用JSON格式
2. **字符编码**: 统一使用UTF-8编码
3. **时间格式**: 使用ISO 8601格式 (YYYY-MM-DDTHH:mm:ssZ)
4. **流式响应**: WebSocket接口支持流式数据传输，适合实时交互场景
5. **错误处理**: 客户端应妥善处理各种错误情况
6. **认证**: 部分接口可能需要认证token
7. **限制**: AI模型调用可能有频率限制，请合理控制调用频率

---

## 更新日志

- **v1.0.0**: 初始版本，包含基础CRUD操作和AI聊天功能
- **v1.1.0**: 增加WebSocket流式聊天和剧情分析功能
- **v1.2.0**: 完善错误处理和响应格式