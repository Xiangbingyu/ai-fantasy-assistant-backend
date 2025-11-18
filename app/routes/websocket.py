from flask import Blueprint, request, jsonify
from flask_socketio import SocketIO, emit, join_room
from zai import ZhipuAiClient
from app.config import Config
from app.models import db, ConversationMessage
from app.logging_config import setup_logging
import json
import logging

# 确保日志配置正确
setup_logging()

websocket_bp = Blueprint('websocket', __name__)
socketio = SocketIO()

client = ZhipuAiClient(api_key=Config.ZHIPU_API_KEY)

# 使用配置好的日志器
logger = logging.getLogger(__name__)

@socketio.on('connect')
def handle_connect():
    """客户端连接时触发"""
    print('客户端已连接')
    emit('connected', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接时触发"""
    print('客户端已断开连接')

@socketio.on('join')
def handle_join(data):
    """客户端加入房间"""
    room = data.get('room', 'default')
    join_room(room)
    emit('joined', {'room': room, 'status': 'joined'})

@socketio.on('chat_stream')
def handle_chat_stream(data):
    """处理流式聊天并保存消息到数据库"""
    try:
        # 解析参数
        history = data.get("messages") or []
        worldview = data.get("worldview") or ""
        master_sitting = data.get("master_sitting") or ""
        background = data.get("background") or ""
        story_analysis = data.get("story_analysis") or ""
        story_guide = data.get("story_guide") or ""
        chapter_id = data.get("chapterId")
        user_id = data.get("userId")
        
        logger.info(f"收到聊天请求 - chapter_id: {chapter_id}, user_id: {user_id}")
        
        # 统一处理 main_characters
        main_characters = data.get("main_characters")
        if isinstance(main_characters, (list, tuple)):
            mc_text = ", ".join(map(str, main_characters))
        elif isinstance(main_characters, dict):
            mc_text = json.dumps(main_characters, ensure_ascii=False)
        else:
            mc_text = str(main_characters) if main_characters else "无明确角色"

        # 构造结构化提示词
        structured_prompt = f"""[Role]
你是一位「沉浸式互动剧本作者」，以第三人称全知视角创作，擅长用细腻笔触构建场景、刻画人心。
「核心人物」需作为剧情核心，笔墨占比最高，其行为、神态、语言需严格贴合设定的性格、身份与风格，且避免重复上几轮出现出现的动作与环境细节，通过新增关键信息推动剧情，拒绝刻板化重复。
其余角色与环境仅作为烘托，服务于核心人物塑造与剧情推进，不得抢占核心戏份。
语言风格需深度契合提供的「世界观」，融入场景动态感与人物情绪张力，所有内容必须自然承接玩家上轮话语的核心意涵，可适度延伸对话情境，让互动更具画面流动感。
**严禁描写玩家的任何动作、神态、对话，仅通过核心人物的反应承接玩家行为，不添加玩家视角的回应内容**

[Core Context]
# 世界观
{worldview or '无特殊设定'}（创作时需将世界观元素融入细节，如器物样式、言谈礼节、环境氛围）

# 核心人物（重点刻画）
{master_sitting}

# 其余关系人物（可偶尔出场）
{mc_text or '无特定人物关系'}（出场需有合理性，在推动剧情或衬托核心人物时出现）

# 玩家背景设定
{background or '无特定玩家背景'}（回应时可适度结合玩家设定，让互动更具针对性，仅通过核心人物的反应体现）

# 剧情状态分析
{story_analysis or '无剧情分析信息'}

# 剧情引导（必须遵循）
{story_guide or '无特定剧情引导，可自由发挥'}（引导需 "润物无声"，通过核心人物的对话提议、动作暗示推动剧情，可通过多轮对话衔接实现剧情引导，避免生硬指令与突兀变化）

请务必在回复中自然融入剧情引导要求，让故事发展贴合用户期望的同时，保持叙事的流畅性与沉浸感。

[Input Handling]
玩家消息中的 "开场白""正文：" 等前缀为系统标记，直接理解内容核心含义即可，回复中无需提及或呼应该前缀，聚焦对话本身的情境延续。

[Output Requirements]
1. 一段 30～100 字的**单段连贯文本**（禁止分段、换行）：
   - 核心人物需包含「动作描写+神态刻画+对话」三要素，逻辑连贯；
   - 允许搭配「人物动作/台词」+「环境/旁白」，但核心人物占主导戏份；
   - 避免 "公式化排列" 要素，让动作、神态、对话自然交织。
2. 禁止出现现代网络梗、OOC 提示、括号解说，语言贴合世界观与角色身份；
3. 直接输出正文内容，**绝对不要**添加任何前缀（如"正文"、"回复"等），聚焦当前对话节点的自然延续，让文字自带 "镜头感"。

[Recent History]
{json.dumps(history, ensure_ascii=False) if history else '无历史对话'}
"""

        messages = [{"role": "system", "content": structured_prompt}] + [{"role":"user","content":"现在我需要你根据最近的历史对话，继续下一个对话节点。"}]

        # 用于累积流式响应内容
        accumulated_content = ""
        chunk_count = 0

        # 创建流式响应
        try:
            logger.info("开始创建流式响应...")
            stream = client.chat.completions.create(
                model="glm-4-plus",
                messages=messages,
                temperature=0.7,
                max_tokens=200,
                stream=True
            )
            logger.info("流式响应创建成功，开始处理数据块...")
            
            # 发送流式响应并累积内容
            for chunk in stream:
                chunk_count += 1
                logger.debug(f"处理第 {chunk_count} 个数据块")
                
                if chunk.choices and len(chunk.choices) > 0 and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    accumulated_content += content
                    logger.debug(f"收到内容: '{content}', 累积长度: {len(accumulated_content)}")
                    
                    emit('chat_stream_data', {
                        'content': content,
                        'finished': False
                    })
                else:
                    logger.debug(f"数据块 {chunk_count} 无内容或格式异常")
            
            logger.info(f"流式处理完成 - 总共处理 {chunk_count} 个数据块, 累积内容长度: {len(accumulated_content)}")
            logger.info(f"AI回复已完成 - 内容: {accumulated_content}")
            
            # 保存AI消息到数据库
            if accumulated_content and chapter_id and user_id:
                logger.info(f"开始保存AI消息到数据库 - chapter_id: {chapter_id}, user_id: {user_id}")
                try:
                    ai_message = ConversationMessage(
                        chapter_id=int(chapter_id),
                        user_id=int(user_id),
                        role='ai',
                        content=f"正文：{accumulated_content}"
                    )
                    db.session.add(ai_message)
                    db.session.commit()
                    logger.info(f"AI消息已保存到数据库 - ID: {ai_message.id}")
                    
                    # 发送完成信号，包含消息ID
                    emit('chat_stream_end', {
                        'finished': True,
                        'message_id': ai_message.id
                    })
                except Exception as db_error:
                    logger.error(f"保存AI消息到数据库失败: {str(db_error)}")
                    db.session.rollback()
                    emit('chat_stream_end', {'finished': True})
            else:
                logger.warning(f"无法保存AI消息 - accumulated_content: {bool(accumulated_content)}, chapter_id: {chapter_id}, user_id: {user_id}")
                # 发送完成信号
                emit('chat_stream_end', {'finished': True})
                
        except Exception as stream_error:
            logger.error(f"流式响应失败: {str(stream_error)}")
            logger.error(f"异常类型: {type(stream_error).__name__}")
            import traceback
            logger.error(f"异常堆栈: {traceback.format_exc()}")
            
            # 如果流式响应失败，降级到普通响应
            logger.info("降级到普通响应模式...")
            response = client.chat.completions.create(
                model="glm-4-plus",
                messages=messages,
                temperature=0.7,
                max_tokens=200
            )
            
            content = response.choices[0].message.content
            accumulated_content = content
            logger.info(f"普通响应完成 - 内容长度: {len(content)}")
            
            # 保存AI消息到数据库
            if content and chapter_id and user_id:
                try:
                    ai_message = ConversationMessage(
                        chapter_id=int(chapter_id),
                        user_id=int(user_id),
                        role='ai',
                        content=f"正文：{content}"
                    )
                    db.session.add(ai_message)
                    db.session.commit()
                    logger.info(f"AI消息已保存到数据库 - ID: {ai_message.id}")
                    
                    # 发送完整响应，包含消息ID
                    emit('chat_stream_data', {
                        'content': content,
                        'finished': True,
                        'message_id': ai_message.id
                    })
                except Exception as db_error:
                    logger.error(f"保存AI消息到数据库失败: {str(db_error)}")
                    db.session.rollback()
                    # 发送完整响应
                    emit('chat_stream_data', {
                        'content': content,
                        'finished': True
                    })
            else:
                # 发送完整响应
                emit('chat_stream_data', {
                    'content': content,
                    'finished': True
                })

    except Exception as e:
        logger.error(f"聊天流式处理异常: {str(e)}")
        emit('chat_stream_error', {'error': str(e)})

@socketio.on('chat_analyze_stream')
def handle_chat_analyze_stream(data):
    """处理流式剧情分析"""
    try:
        history = data.get("messages") or []
        worldview = data.get("worldview") or ""
        master_sitting = data.get("master_sitting") or ""
        background = data.get("background") or ""
        
        # 统一处理 main_characters
        main_characters = data.get("main_characters")
        if isinstance(main_characters, (list, tuple)):
            mc_text = ", ".join(map(str, main_characters))
        elif isinstance(main_characters, dict):
            mc_text = json.dumps(main_characters, ensure_ascii=False)
        else:
            mc_text = str(main_characters) if main_characters else "无明确角色"

        # 构造结构化提示词
        structured_prompt = f"""[Role]
你是专业剧情分析师，从对话历史提取关键信息，结合世界观、角色与玩家设定，生成简短文本报告，助力后续创作。

[Core Context]
# 世界观
{worldview or '无特殊设定'}

# 核心人物
{master_sitting}

# 其余关系人物
{mc_text or '无特定人物关系'}

# 玩家背景设定
{background or '无特定玩家背景'}

[Current Conversation History]
{json.dumps(history, ensure_ascii=False) if history else '无历史对话'}

[Output Requirements]
用流畅中文段落输出，每部分空行隔开，总字数控制在 300 字内：
1. 剧情概览：用80字总结当前剧情走向。
2. 关键事件：按时间顺序列出1-3个最重要的事件，每条20字以内，用"·"开头。
3. 角色与玩家状态：40 字内说明核心角色与玩家的情感 / 立场。
4. 关键伏笔：提 1-2 个影响后续剧情的重要信息。
5. 当前悬念：30 字内点明主要矛盾或待解问题。

无需任何标题或前缀，直接输出正文即可。
"""

        messages = [
            {"role": "system", "content": structured_prompt},
            {"role": "user", "content": "请根据提供的对话历史和上下文信息，分析当前剧情情况，提取关键事件并整理长期记忆。"}
        ]

        # 创建流式响应
        try:
            stream = client.chat.completions.create(
                model="glm-4-plus",
                messages=messages,
                temperature=0.3,
                max_tokens=700,
                stream=True
            )
            
            # 发送流式响应
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    emit('chat_analyze_stream_data', {
                        'content': content,
                        'finished': False
                    })
            
            # 发送完成信号
            emit('chat_analyze_stream_end', {'finished': True})
        except Exception as stream_error:
            # 如果流式响应失败，降级到普通响应
            response = client.chat.completions.create(
                model="glm-4-plus",
                messages=messages,
                temperature=0.3,
                max_tokens=700
            )
            
            content = response.choices[0].message.content
            # 发送完整响应
            emit('chat_analyze_stream_data', {
                'content': content,
                'finished': True
            })

    except Exception as e:
        emit('chat_analyze_stream_error', {'error': str(e)})

# WebSocket蓝图初始化函数
def init_websocket(socketio_app):
    """初始化WebSocket配置"""
    socketio_app.init_app(websocket_bp)
    globals()['socketio'] = socketio_app