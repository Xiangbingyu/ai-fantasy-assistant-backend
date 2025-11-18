# 部署环境日志配置说明

## 问题分析
在云服务器上运行时，日志输出不完整，只显示基本的HTTP请求信息，而本地环境能显示完整的AI回复和数据库操作日志。

**可能的原因：**
1. 流式响应处理在云服务器环境中提前退出
2. 日志缓冲问题
3. 环境变量差异
4. 网络连接超时
5. Python包版本差异

## 解决方案
1. **统一日志配置**: 创建了 `app/logging_config.py` 统一管理日志配置
2. **强制标准输出**: 确保所有日志都输出到 `sys.stdout`
3. **详细日志格式**: 包含时间戳、模块名、日志级别和消息内容
4. **增强调试**: 添加流式处理的详细调试日志
5. **异常处理**: 完善异常捕获和堆栈跟踪

## 修改的文件
- `app/logging_config.py` (新增): 统一日志配置，启用DEBUG级别
- `run.py`: 使用新的日志配置
- `app/routes/websocket.py`: 增强流式处理日志和异常处理
- `test_stream.py` (新增): 流式响应测试脚本
- `check_environment.py` (新增): 环境检测脚本

## 诊断步骤

### 1. 环境检测
在云服务器上运行：
```bash
cd /path/to/ai-fantasy-assistant-backend
python check_environment.py
```

### 2. 流式响应测试
在云服务器上运行：
```bash
cd /path/to/ai-fantasy-assistant-backend
python test_stream.py
```

### 3. 启动应用并观察日志
```bash
export PYTHONUNBUFFERED=1
python run.py
```

## 云服务器部署建议

### 环境变量设置
```bash
export PYTHONUNBUFFERED=1
export FLASK_ENV=production
export FLASK_DEBUG=false
```

### systemd 服务配置
```ini
[Unit]
Description=AI Fantasy Assistant Backend
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/ai-fantasy-assistant-backend
Environment=PYTHONUNBUFFERED=1
Environment=FLASK_ENV=production
ExecStart=/usr/bin/python3 /path/to/ai-fantasy-assistant-backend/run.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ai-fantasy-assistant

[Install]
WantedBy=multi-user.target
```

### Docker 部署
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

CMD ["python", "run.py"]
```

## 预期日志输出
启动后应该看到类似输出:
```
2025-11-19 00:08:44 - app.logging_config - INFO - ============================================================
2025-11-19 00:08:44 - app.logging_config - INFO - AI幻想助手后端服务启动
2025-11-19 00:08:44 - app.logging_config - INFO - 启动时间: 2025-11-19 00:08:44
2025-11-19 00:08:44 - app.logging_config - INFO - 日志级别: DEBUG
2025-11-19 00:08:44 - app.logging_config - INFO - 日志输出: 标准输出
2025-11-19 00:08:44 - app.logging_config - INFO - ============================================================
2025-11-19 00:08:45 - app.routes.websocket - INFO - 收到聊天请求 - chapter_id: 1, user_id: 1
2025-11-19 00:08:45 - app.routes.websocket - INFO - 开始创建流式响应...
2025-11-19 00:08:45 - app.routes.websocket - INFO - 流式响应创建成功，开始处理数据块...
2025-11-19 00:08:48 - app.routes.websocket - INFO - 流式处理完成 - 总共处理 X 个数据块, 累积内容长度: XX
2025-11-19 00:08:48 - app.routes.websocket - INFO - AI回复已完成 - 内容: XXX
2025-11-19 00:08:48 - app.routes.websocket - INFO - 开始保存AI消息到数据库 - chapter_id: 1, user_id: 1
2025-11-19 00:08:48 - app.routes.websocket - INFO - AI消息已保存到数据库 - ID: 744
```

## 故障排除

### 如果仍然看不到详细日志：
1. 检查是否设置了 `PYTHONUNBUFFERED=1`
2. 确认没有日志重定向 (`> output.txt 2>&1`)
3. 检查容器或云平台的日志收集配置
4. 运行环境检测脚本对比差异

### 如果流式处理异常：
1. 运行 `test_stream.py` 测试流式响应
2. 检查网络连接到 `open.bigmodel.cn`
3. 验证API密钥是否正确
4. 查看是否有超时或连接中断

### 如果数据库保存失败：
1. 检查数据库连接配置
2. 验证数据库表是否存在
3. 检查数据库权限
4. 查看数据库日志

## 联系支持
如果问题仍然存在，请提供：
1. `check_environment.py` 的输出
2. `test_stream.py` 的输出
3. 完整的应用启动日志
4. 云服务器类型和配置信息