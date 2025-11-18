import logging
import sys
from datetime import datetime

def setup_logging():
    """配置应用日志系统"""
    
    # 创建日志格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 设置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 清除现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 设置特定模块的日志级别
    logging.getLogger('httpx').setLevel(logging.INFO)
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # 确保我们的应用日志器使用正确的配置
    app_logger = logging.getLogger('app.routes.websocket')
    app_logger.setLevel(logging.INFO)
    
    return root_logger

def log_startup_info():
    """记录启动信息"""
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("AI幻想助手后端服务启动")
    logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("日志级别: INFO")
    logger.info("日志输出: 标准输出")
    logger.info("=" * 60)