from flask import Blueprint, request, jsonify
from zai import ZhipuAiClient
from app.config import Config
import json

llm_bp = Blueprint('llm', __name__, url_prefix='/api')

client = ZhipuAiClient(api_key=Config.ZHIPU_API_KEY)

@llm_bp.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True) or {}
        history = data.get("messages") or []

        print(data)

        # 提取上下文字段
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

        print("世界观:", worldview)
        print("主要角色 sitting:", master_sitting)
        print("背景信息:", background)
        print("主要角色信息:", mc_text)
        # 构造结构化提示词
        structured_prompt = f"""[Role]
你是一位「沉浸式互动剧本作者」，用第三人称全知视角写作。
你可以描写任何角色（包括核心人物、其余关系人物、环境），但**核心人物**必须是笔墨最多、性格最鲜活的那一位，其行为需严格遵循设定的性格、身份与说话风格。  
语言风格参照提供的「世界观」与「角色设定」，保持古风、简洁、带画面感，所有内容必须**承接玩家上次说的话**，自然延续对话节点（而非修饰玩家上轮话语）。

[Core Context]
# 世界观
{worldview or '无特殊设定'}

# 核心人物（重点刻画）
{master_sitting}

# 其余关系人物（可偶尔出场）
{mc_text or '无特定人物关系'}

# 玩家信息背景
{background or '无特定场景'}

[Output Requirements]
1. 一段 30～150 字回复：
   - 核心人物需包含「动作描写+神态刻画+对话」三要素，逻辑连贯；
   - 允许搭配「人物动作/台词」+「环境/旁白」，但核心人物占主导戏份；
2. 禁止出现现代网络梗、OOC 提示、括号解说，语言贴合世界观与角色身份；
3. 直接输出正文，不要带“【角色】：”这类前缀，聚焦当前对话节点的自然延续。

[Recent History]
{json.dumps(history, ensure_ascii=False) if history else '无历史对话'}
"""

        messages = [{"role": "system", "content": structured_prompt}] + [{"role":"user","content":"现在我需要你根据最近的历史对话，继续下一个对话节点。"}]

        response = client.chat.completions.create(
            model="glm-4-plus",
            messages=messages,
            temperature=0.5
        )

        print("大模型原始响应：", response)
        print("AI回复内容：", response.choices[0].message.content)

        return jsonify({"response": response.choices[0].message.content})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@llm_bp.route("/chat/suggestions", methods=["POST"])
def chat_suggestions():
    try:
        data = request.get_json(silent=True) or {}
        history = data.get("messages") or []

        # 统一组装主要角色信息
        main_characters = data.get("main_characters")
        if isinstance(main_characters, (list, tuple)):
            mc_text = ", ".join(map(str, main_characters))
        elif isinstance(main_characters, dict):
            mc_text = json.dumps(main_characters, ensure_ascii=False)
        else:
            mc_text = str(main_characters) if main_characters else ""

        # 构造 system 提示
        system_prompt = f"""[Role]
你是一个对话回复辅助生成器，负责基于以下上下文和历史对话，为用户生成符合场景的下一条回复示例。需完全贴合世界观设定、角色特征和对话氛围。

[Core Context]
世界观：{data.get("worldview") or "无特殊设定"}
核心人物 sitting：{data.get("master_sitting") or "无特定人物关系"}
其余关系人物信息：{mc_text}
玩家背景：{data.get("background") or "无特定场景"}

[Output Requirements]
1. 数量：必须生成6条回复示例，每条为独立的可能延续方向
2. 内容：需符合当前对话逻辑，贴合角色身份与世界观，避免重复历史对话内容
3. 风格：简洁自然（单条20-80字），中文表达，语气符合场景氛围
4. 格式：严格输出JSON数组，结构为{{\"content\": \"示例回复\"}}，无任何额外内容。
5. 禁忌：禁止添加解释、注释、代码块标记（如```json），禁止非JSON内容，禁止重复示例。

[Format Example]
[
  {{\"content\": "（动作）神态，对话内容"}},
  {{\"content\": "（动作）神态，对话内容"}},
  {{\"content\": "（动作）神态，对话内容"}},
  {{\"content\": "（动作）神态，对话内容"}},
  {{\"content\": "（动作）神态，对话内容"}},
  {{\"content\": "（动作）神态，对话内容"}}
]

[Current Conversation History]
{json.dumps(history, ensure_ascii=False) if history else "无历史对话"}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "现在我需要你生成6条回复示例"}
        ]

        response = client.chat.completions.create(
            model="glm-3-turbo",
            messages=messages,
            temperature=0.6,
            max_tokens=600
        )

        text = response.choices[0].message.content

        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return jsonify({"suggestions": parsed})
            return jsonify({"raw": text})
        except Exception:
            return jsonify({"raw": text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@llm_bp.route("/novel", methods=["POST"])
def generate_novel():
    try:
        # 获取前端传递的参数
        data = request.get_json()
        if not data or "prompt" not in data:
            return jsonify({"error": "缺少小说生成提示信息"}), 400

        system_prompt = (
            "你是一位资深小说家，请根据以下提示创作一篇风格契合、详略得当、细节丰富的小说。"
            "生成的内容需严格遵循格式要求：第一段话必须是章节标题，无需任何开场白（如‘好的，故事开始了’等引导语），直接以标题开头进行创作。"
        )

        # 新增：从请求体获取上下文字段并组装为第二条 system 消息
        worldview = data.get("worldview")
        master_sitting = data.get("master_sitting")
        main_characters = data.get("main_characters")
        background = data.get("background")

        if isinstance(main_characters, (list, tuple)):
            mc_text = ", ".join([str(x) for x in main_characters])
        elif isinstance(main_characters, dict):
            mc_text = json.dumps(main_characters, ensure_ascii=False)
        else:
            mc_text = str(main_characters) if main_characters is not None else ""

        context_prompt = (
            f"世界观：{worldview or ''}\n"
            f"主控设定：{master_sitting or ''}\n"
            f"主要角色：{mc_text}\n"
            f"章节背景：{background or ''}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": context_prompt},
            {"role": "user", "content": data["prompt"]}
        ]

        # 调用glm-4.6模型生成小说
        response = client.chat.completions.create(
            model="glm-4.6",
            messages=messages,
            thinking={"type": "enabled"},
            temperature=0.7
        )

        print("大模型原始响应：", response)
        print("AI回复内容：", response.choices[0].message.content)

        return jsonify({"response": response.choices[0].message.content})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
