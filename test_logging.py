#!/usr/bin/env python3
"""
日志测试脚本
用于验证在不同环境中日志配置是否正确工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.logging_config import setup_logging, log_startup_info
import logging

def test_logging():
    """测试日志功能"""
    print("开始测试日志配置...")
    
    # 设置日志
    setup_logging()
    log_startup_info()
    
    # 获取日志器
    logger = logging.getLogger(__name__)
    
    # 测试不同级别的日志
    logger.info("这是一条测试信息日志")
    logger.warning("这是一条测试警告日志")
    logger.error("这是一条测试错误日志")
    
    # 测试应用模块日志
    app_logger = logging.getLogger('app.routes.websocket')
    app_logger.info("模拟AI回复已完成 - 内容: 这是测试的AI回复内容")
    app_logger.info("模拟AI消息已保存到数据库 - ID: 12345")
    
    # 测试第三方库日志
    httpx_logger = logging.getLogger('httpx')
    httpx_logger.info("模拟HTTP请求日志")
    
    print("日志测试完成！请检查上述输出是否包含所有日志信息。")

if __name__ == "__main__":
    test_logging()