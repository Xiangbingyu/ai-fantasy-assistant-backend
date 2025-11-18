#!/usr/bin/env python3
"""
流式响应测试脚本
用于测试在云服务器环境中流式响应是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.logging_config import setup_logging, log_startup_info
from app.config import Config
from zai import ZhipuAiClient
import logging

def test_stream_response():
    """测试流式响应"""
    # 设置日志
    setup_logging()
    log_startup_info()
    
    logger = logging.getLogger(__name__)
    
    try:
        # 初始化客户端
        client = ZhipuAiClient(api_key=Config.ZHIPU_API_KEY)
        logger.info("ZhipuAI客户端初始化成功")
        
        # 构造测试消息
        messages = [
            {"role": "system", "content": "你是一个测试助手，请简单回复'测试成功'"},
            {"role": "user", "content": "请回复测试消息"}
        ]
        
        logger.info("开始测试流式响应...")
        
        # 测试流式响应
        stream = client.chat.completions.create(
            model="glm-4-plus",
            messages=messages,
            temperature=0.7,
            max_tokens=50,
            stream=True
        )
        
        logger.info("流式响应创建成功，开始处理数据块...")
        
        accumulated_content = ""
        chunk_count = 0
        
        for chunk in stream:
            chunk_count += 1
            logger.debug(f"处理第 {chunk_count} 个数据块")
            logger.debug(f"数据块类型: {type(chunk)}")
            logger.debug(f"数据块内容: {chunk}")
            
            if hasattr(chunk, 'choices') and chunk.choices:
                logger.debug(f"choices长度: {len(chunk.choices)}")
                if hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'content'):
                    content = chunk.choices[0].delta.content
                    if content:
                        accumulated_content += content
                        logger.debug(f"收到内容: '{content}', 累积长度: {len(accumulated_content)}")
                    else:
                        logger.debug("内容为空")
                else:
                    logger.debug("delta或content不存在")
            else:
                logger.debug("choices不存在或为空")
        
        logger.info(f"流式处理完成 - 总共处理 {chunk_count} 个数据块")
        logger.info(f"累积内容长度: {len(accumulated_content)}")
        logger.info(f"完整内容: '{accumulated_content}'")
        
        if accumulated_content:
            logger.info("✅ 流式响应测试成功")
        else:
            logger.warning("⚠️ 流式响应测试失败 - 没有收到任何内容")
            
    except Exception as e:
        logger.error(f"❌ 流式响应测试失败: {str(e)}")
        logger.error(f"异常类型: {type(e).__name__}")
        import traceback
        logger.error(f"异常堆栈: {traceback.format_exc()}")

def test_normal_response():
    """测试普通响应"""
    logger = logging.getLogger(__name__)
    
    try:
        # 初始化客户端
        client = ZhipuAiClient(api_key=Config.ZHIPU_API_KEY)
        logger.info("开始测试普通响应...")
        
        # 构造测试消息
        messages = [
            {"role": "system", "content": "你是一个测试助手，请简单回复'测试成功'"},
            {"role": "user", "content": "请回复测试消息"}
        ]
        
        # 测试普通响应
        response = client.chat.completions.create(
            model="glm-4-plus",
            messages=messages,
            temperature=0.7,
            max_tokens=50,
            stream=False
        )
        
        content = response.choices[0].message.content
        logger.info(f"普通响应完成 - 内容: '{content}'")
        logger.info("✅ 普通响应测试成功")
        
    except Exception as e:
        logger.error(f"❌ 普通响应测试失败: {str(e)}")

if __name__ == "__main__":
    print("=" * 60)
    print("开始流式响应诊断测试")
    print("=" * 60)
    
    # 先测试普通响应
    print("\n1. 测试普通响应...")
    test_normal_response()
    
    # 再测试流式响应
    print("\n2. 测试流式响应...")
    test_stream_response()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)