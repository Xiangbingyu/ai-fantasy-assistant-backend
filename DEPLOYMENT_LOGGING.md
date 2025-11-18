# 部署环境日志配置说明

## 问题分析
在云服务器上运行时，日志输出不完整，只显示基本的HTTP请求信息，而本地环境能显示完整的AI回复和数据库操作日志。

## 解决方案
1. **统一日志配置**: 创建了 `app/logging_config.py` 统一管理日志配置
2. **强制标准输出**: 确保所有日志都输出到 `sys.stdout`
3. **详细日志格式**: 包含时间戳、模块名、日志级别和消息内容
4. **第三方库日志级别**: 设置 `httpx` 和 `werkzeug` 的日志级别

## 修改的文件
- `app/logging_config.py` (新增): 统一日志配置
- `run.py`: 使用新的日志配置
- `app/routes/websocket.py`: 简化日志配置，使用统一配置

## 云服务器部署建议
1. 确保启动命令没有重定向输出:
   ```bash
   python run.py  # 不要使用 > output.txt 2>&1
   ```

2. 如果使用 systemd 或其他进程管理器，确保配置正确:
   ```ini
   [Service]
   ExecStart=/usr/bin/python3 /path/to/run.py
   StandardOutput=journal
   StandardError=journal
   SyslogIdentifier=ai-fantasy-assistant
   ```

3. 检查环境变量:
   ```bash
   export PYTHONUNBUFFERED=1
   export FLASK_ENV=production
   ```

## 验证方法
启动后应该看到类似输出:
```
2025-11-18 23:53:46 - app.logging_config - INFO - ============================================================
2025-11-18 23:53:46 - app.logging_config - INFO - AI幻想助手后端服务启动
2025-11-18 23:53:46 - app.logging_config - INFO - 启动时间: 2025-11-18 23:53:46
2025-11-18 23:53:46 - app.logging_config - INFO - 日志级别: INFO
2025-11-18 23:53:46 - app.logging_config - INFO - 日志输出: 标准输出
2025-11-18 23:53:46 - app.logging_config - INFO - ============================================================
```

## 如果问题仍然存在
1. 检查服务器的日志缓冲设置
2. 确认没有其他日志配置覆盖我们的设置
3. 检查容器或云平台的日志收集配置