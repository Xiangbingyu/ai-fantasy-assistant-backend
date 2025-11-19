# 小说生成API异步化说明

## 概述
将原来的同步小说生成接口改为异步处理，解决超时问题和避免用户长时间等待。

## 新的API接口

### 1. 提交小说生成任务
**接口**: `POST /api/novel`

**请求参数**: 与原来相同
```json
{
  "prompt": "对话内容",
  "worldview": "世界观",
  "master_sitting": "核心人物设定",
  "main_characters": ["角色1", "角色2"],
  "background": "玩家背景"
}
```

**响应**: 立即返回任务ID
```json
{
  "task_id": "uuid-string",
  "status": "accepted",
  "message": "小说生成任务已接受，正在处理中..."
}
```

### 2. 查询任务状态
**接口**: `GET /api/novel/status/<task_id>`

**响应**: 任务状态信息
```json
{
  "status": "processing|completed|failed",
  "progress": "处理进度描述",
  "created_at": "创建时间",
  "completed_at": "完成时间",
  "result": "生成的小说内容（仅在status为completed时有值）",
  "error": "错误信息（仅在status为failed时有值）"
}
```

### 3. 清理过期任务
**接口**: `POST /api/novel/cleanup`

**响应**: 清理结果
```json
{
  "message": "已清理 X 个过期任务",
  "cleaned_tasks": ["task_id1", "task_id2"]
}
```

## WebSocket事件通知

系统会通过WebSocket推送以下事件：

### 1. 任务更新
**事件**: `novel_task_update`
```json
{
  "task_id": "uuid-string",
  "status": "processing",
  "progress": "正在调用 AI 模型生成内容..."
}
```

### 2. 任务完成
**事件**: `novel_task_complete`
```json
{
  "task_id": "uuid-string",
  "status": "completed",
  "result": "生成的小说内容"
}
```

### 3. 任务失败
**事件**: `novel_task_error`
```json
{
  "task_id": "uuid-string",
  "status": "failed",
  "error": "错误信息"
}
```

## 前端集成建议

### 方案1: 轮询查询
1. 提交任务获得task_id
2. 定时轮询 `/api/novel/status/<task_id>` 查询状态
3. 当status为completed或failed时停止轮询

### 方案2: WebSocket监听（推荐）
1. 建立WebSocket连接
2. 监听上述WebSocket事件
3. 根据事件类型更新UI状态

## 任务生命周期

1. **accepted**: 任务已接受，正在排队处理
2. **processing**: 正在生成小说
3. **completed**: 生成完成，结果可用
4. **failed**: 生成失败，查看错误信息

## 内存管理

- 系统会自动清理超过24小时的已完成任务
- 可通过 `/api/novel/cleanup` 手动清理过期任务
- 任务状态存储在内存中，重启服务会丢失

## 优势

1. **无超时**: 避免HTTP请求超时问题
2. **用户体验**: 用户无需等待，可以继续其他操作
3. **实时反馈**: 通过WebSocket提供实时进度更新
4. **可扩展**: 支持多个任务并发处理
5. **容错性**: 单个任务失败不影响其他任务