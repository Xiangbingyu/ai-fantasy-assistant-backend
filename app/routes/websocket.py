from flask import Blueprint, request, jsonify
from flask_socketio import SocketIO, emit, join_room
from zai import ZhipuAiClient
from app.config import Config
from app.models import db, ConversationMessage
import json
import logging

websocket_bp = Blueprint('websocket', __name__)
socketio = SocketIO(cors_allowed_origins="*")

client = ZhipuAiClient(api_key=Config.ZHIPU_API_KEY)

# 配置日志
logging.basicConfig(level=logging.INFO)
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

        # 创建流式响应
        try:
            stream = client.chat.completions.create(
                model="glm-4-plus",
                messages=messages,
                temperature=0.7,
                max_tokens=200,
                stream=True
            )
            
            # 发送流式响应并累积内容
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    accumulated_content += content
                    emit('chat_stream_data', {
                        'content': content,
                        'finished': False
                    })
            logger.info(f"AI回复已完成 - 内容: {accumulated_content}")
            
            # 保存AI消息到数据库
            if accumulated_content and chapter_id and user_id:
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
                # 发送完成信号
                emit('chat_stream_end', {'finished': True})
                
        except Exception as stream_error:
            logger.error(f"流式响应失败: {str(stream_error)}")
            # 如果流式响应失败，降级到普通响应
            response = client.chat.completions.create(
                model="glm-4-plus",
                messages=messages,
                temperature=0.7,
                max_tokens=200
            )
            
            content = response.choices[0].message.content
            accumulated_content = content
            
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

@socketio.on('world-creator')
def handle_world_creator(data):
    """处理世界观创建请求，使用function call方式生成结构化的世界观设定"""
    try:
        # 解析参数
        user_message = data.get("message", "")
        history = data.get("history", [])
        user_id = data.get("userId", None)
        
        logger.info(f"收到世界观创建请求 - user_id: {user_id}")
        
        # 如果没有用户消息，返回错误
        if not user_message:
            emit('world_creator_error', {'error': '用户消息不能为空'})
            return
        
        # 定义function call的工具
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "create_world_setting",
                    "description": "创建详细的世界观设定，包括世界背景、角色信息和初始剧情",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "world_name": {
                                "type": "string",
                                "description": "世界的名称"
                            },
                            "world_description": {
                                "type": "string",
                                "description": "世界观的详细描述，包括地理环境、历史背景、文化特色、社会结构等"
                            },
                            "character_name": {
                                "type": "string",
                                "description": "AI主要扮演角色的名字，非用户角色"
                            },
                            "appearance": {
                                "type": "string",
                                "description": "AI主要扮演角色的外貌特征描述"
                            },
                            "clothing_style": {
                                "type": "string",
                                "description": "AI主要扮演角色的服饰风格描述"
                            },
                            "character_background": {
                                "type": "string",
                                "description": "AI主要扮演角色的背景故事描述"
                            },
                            "personality_traits": {
                                "type": "string",
                                "description": "AI主要扮演角色的性格特征描述"
                            },
                            "language_style": {
                                "type": "string",
                                "description": "AI主要扮演角色的语言风格描述"
                            },
                            "behavior_logic": {
                                "type": "string",
                                "description": "AI主要扮演角色的行为逻辑描述"
                            },
                            "psychological_traits": {
                                "type": "string",
                                "description": "AI主要扮演角色的心理特质描述"
                            },
                            "chapter_name": {
                                "type": "string",
                                "description": "章节的名称"
                            },
                            "opening_line": {
                                "type": "string",
                                "description": "章节的开场白，需为引导故事情节开始的动态场景描写，包含时间、角色互动、背景回顾、日常细节、情感铺垫和动作描写，让用户能快速代入剧情，自然开启故事"
                            },
                            "user_role": {
                                "type": "string",
                                "description": "用户在故事中的角色，需包含详细的身份背景、职业/生活状态、人际关系、性格特质、核心矛盾或坚持，内容具体且有画面感，避免简单笼统的描述"
                            },
                            "other_character_names": {
                                "type": "array",
                                "description": "其余人物的名字列表",
                                "items": {
                                    "type": "string",
                                    "description": "人物名字"
                                }
                            },
                            "other_character_backgrounds": {
                                "type": "array",
                                "description": "其余人物的背景故事列表，与名字列表一一对应",
                                "items": {
                                    "type": "string",
                                    "description": "人物背景故事"
                                }
                            }
                        },
                        "required": ["world_name", "world_description", "character_name", "appearance", 
                                    "clothing_style", "character_background", "personality_traits", 
                                    "language_style", "behavior_logic", "psychological_traits", 
                                    "chapter_name", "opening_line", "user_role", "other_character_names", "other_character_backgrounds"]
                    }
                }
            }
        ]

        # 构造世界观创建的提示词
        structured_prompt = f"""[Role]
你是一位专业的世界观设定师，擅长创建丰富、连贯、有深度的虚构世界。

[Output Requirements]
1. 请使用提供的create_world_setting工具来生成结构化的世界观设定。
2. 根据用户的需求，创建详细且有创意的世界观设定。
3. 确保所有参数都有详细且合理的内容。
4. 必须在other_character_names和other_character_backgrounds字段中生成至少一个其余人物的信息，两个列表需要一一对应。
5. 如果有历史对话，请基于之前生成的内容进行细节修改或扩展，保持连贯性。
6. 严格按照工具定义的参数格式输出，不要有任何额外的解释或说明。
7. 重点要求：opening_line（开场白）必须为引导故事情节开始的动态场景描写，需包含以下要素：
   - 明确的时间节点（如清晨、午后、黄昏等）
   - 角色间的互动或近距离场景（如身边的人、共处的空间）
   - 简要的背景回顾（如共同经历的时光、当前生活状态的由来）
   - 生活化的细节描写（如人物的状态、环境的小细节）
   - 自然的情感铺垫（如对现状的感受、对未来的隐约期待）
   - 推动剧情开始的动作描写（如准备出门、接到消息、发现异常等）
   示例风格："今天，你早早的就醒来，莉亚还在你身边呼呼大睡。自从你们离开故乡，出来打拼已经过去了三年，你已经从懵懵懂懂的少年变成了青年，而莉亚也褪去了稚气的青涩。这三年，你们大部分时间都在工会干活，有时候会去打些杂货，有时候会和别人组队讨伐一些哥布林和史莱姆。儿时讨伐魔王的梦想似乎已经在与莉亚的粗茶淡饭的生活中逐渐磨灭了。但这样的生活，你并不讨厌。你摇了摇头，看了看一旁莉亚的睡颜，帮她捋了捋脸上的发丝，随后穿上衣服准备出门锻炼了。"
   禁止生成静态场景描写（如仅描述人物站在某地、望向远方等无互动、无动作的内容）。
8. 核心要求：user_role（用户角色）必须详细具体，包含至少3个维度的信息（如身份转变、职业/生活状态、人际关系、性格特质、核心坚持/矛盾、生活细节等），参考以下示例风格：
   - 示例1："前企业见习生，现辞职做自由撰稿人；私下继续写异种观察笔记，但对克莉丝汀下不了刀。目前与克莉丝汀在旧公寓 4 楼 404 室同居 47 天，两室一厅，门窗已多处被蛛丝加固。"
   - 示例2："曾是村落里最有天赋的少年战士，如今专注于日常锻炼保持体能；性格内敛寡言但正义感极强，童年时多次保护受欺负的莉亚，对她始终抱着纯粹的兄长式守护之情，从未逾矩。"
   禁止生成简单笼统的描述（如"亚瑟的忠实伙伴"、"主角的朋友"等缺乏具体信息的内容）。
"""

        # 构建消息列表
        messages = [
            {"role": "system", "content": structured_prompt}
        ]
        
        # 添加历史对话
        if history:
            messages.extend(history)
            
        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})

        # 创建function call响应
        try:
            response = client.chat.completions.create(
                model="glm-4-plus",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=2000
            )
            
            # 获取function call结果
            function_call_result = response.choices[0].message.tool_calls[0] if response.choices[0].message.tool_calls else None
            
            if function_call_result:
                # 直接返回原始的function call调用信息给前端
                # 构建原始function call数据结构
                function_call_data = {
                    'id': function_call_result.id,
                    'type': function_call_result.type,
                    'function': {
                        'name': function_call_result.function.name,
                        'arguments': function_call_result.function.arguments
                    }
                }
                emit('world_creator_data', {
                    'content': function_call_data,
                    'finished': True
                })
                logger.info(f"世界观创建function call成功 - 函数名: {function_call_result.function.name}")
            else:
                # 如果没有返回function call，降级处理
                fallback_messages = [
                    {"role": "system", "content": "你是一位专业的世界观设定师，请直接回答用户的问题。"},
                    {"role": "user", "content": user_message}
                ]
                
                fallback_response = client.chat.completions.create(
                    model="glm-4-plus",
                    messages=fallback_messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                content = fallback_response.choices[0].message.content
                emit('world_creator_data', {
                    'content': content,
                    'finished': True
                })
            
            # 发送完成信号
            emit('world_creator_end', {'finished': True})
                
        except Exception as e:
            logger.error(f"Function call处理异常: {str(e)}")
            # 降级处理
            fallback_messages = [
                {"role": "system", "content": "你是一位专业的世界观设定师，请直接回答用户的问题。"},
                {"role": "user", "content": user_message}
            ]
            
            try:
                fallback_response = client.chat.completions.create(
                    model="glm-4-plus",
                    messages=fallback_messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                content = fallback_response.choices[0].message.content
                emit('world_creator_data', {
                    'content': content,
                    'finished': True
                })
            except Exception as fallback_error:
                logger.error(f"降级处理失败: {str(fallback_error)}")
                emit('world_creator_error', {'error': f'处理失败: {str(fallback_error)}'})

    except Exception as e:
        logger.error(f"世界观创建处理异常: {str(e)}")
        emit('world_creator_error', {'error': str(e)})

# WebSocket蓝图初始化函数
def init_websocket(socketio_app):
    """初始化WebSocket配置"""
    socketio_app.init_app(websocket_bp)
    globals()['socketio'] = socketio_app