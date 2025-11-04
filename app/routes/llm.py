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
        # 获取剧情分析参数
        story_analysis = data.get("story_analysis") or ""
        # 获取剧情引导参数
        story_guide = data.get("story_guide") or ""

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
        print("玩家背景设定:", background)
        print("主要角色信息:", mc_text)
        print("剧情分析:", story_analysis)
        print("剧情引导:", story_guide)
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

# 玩家背景设定
{background or '无特定玩家背景'}

# 剧情状态分析
{story_analysis or '无剧情分析信息'}

# 剧情引导（必须遵循）
{story_guide or '无特定剧情引导，可自由发挥'}

请务必在回复中体现剧情引导的要求，确保故事发展符合用户期望的方向。

[Input Handling]
请注意：玩家消息可能包含"开场白"或"正文："前缀，这是系统添加的标记，请直接理解内容含义，不要在回复中重复或强调这个前缀。

[Output Requirements]
1. 一段 30～150 字回复：
   - 核心人物需包含「动作描写+神态刻画+对话」三要素，逻辑连贯；
   - 允许搭配「人物动作/台词」+「环境/旁白」，但核心人物占主导戏份；
2. 禁止出现现代网络梗、OOC 提示、括号解说，语言贴合世界观与角色身份；
3. 直接输出正文内容，**绝对不要**添加任何前缀（如"正文"、"回复"、"【角色】："等），聚焦当前对话节点的自然延续。

[Recent History]
{json.dumps(history, ensure_ascii=False) if history else '无历史对话'}
"""

        messages = [{"role": "system", "content": structured_prompt}] + [{"role":"user","content":"现在我需要你根据最近的历史对话，继续下一个对话节点。"}]

        response = client.chat.completions.create(
            model="glm-4-plus",
            messages=messages,
            temperature=0.7,
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
核心人物设定：{data.get("master_sitting") or "无特定人物关系"}
其余关系人物信息：{mc_text}
玩家背景：{data.get("background") or "无特定场景"}

[Output Requirements]
1. 数量：必须生成6条回复示例，每条为独立的可能延续方向
2. 视角：以玩家扮演的身份或者“你”为主语，写出「动作+神态+对话」或者「动作/神态」+「环境/对话」；可含内心闪念，但镜头始终贴在玩家身上，贴合玩家行为与情感。
3. 内容：必须承接上轮对话，自然推进情节；避免重复历史台词。
4. 风格：简洁自然，20-80字，中文，贴合世界观与角色身份。
4. 格式：严格输出JSON数组，结构为{{\"content\": \"示例回复\"}}，无任何额外内容。
5. 禁忌：禁止添加解释、注释、代码块标记（如```json），禁止非JSON内容，禁止重复示例。

[Format Example]
[
  {{\"content\": "你下意识屏住呼吸，掌心贴上她冰凉的指尖。“那就别忘，把这味道刻进记忆里。”"}},
  {{\"content\": "你微微低头，让她的额头抵在你肩窝，声音轻得像怕惊动星屑。“我在，不会走。”"}},
  {{\"content\": "你收紧手臂，喉结滚动了一瞬。“要是不够，再靠近一点。”"}},
  {{\"content\": "林坤豪任她攥皱袖口，心跳声在寂静里放大。“别怕，这是我们一起活着的证据。”"}},
  {{\"content\": "林坤豪用拇指擦过她睫毛上的星屑，低声笑。“灯塔会灭，我不会。”"}},
  {{\"content\": "林坤豪感受到她的颤抖，心里一颤，轻轻将她抱进怀里。"}}
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
            temperature=0.7,
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

@llm_bp.route("/chat/analyze", methods=["POST"])
def analyze_story():
    try:
        data = request.get_json(silent=True) or {}
        history = data.get("messages") or []

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

        print("开始分析剧情:")
        print("世界观:", worldview)
        print("主要角色 setting:", master_sitting)
        print("玩家背景设定:", background)
        print("主要角色信息:", mc_text)

        # 构造结构化提示词，用于剧情分析
        structured_prompt = f"""[Role]
你是一位专业的剧情分析师，擅长从对话历史中提取关键信息，并整理成简短易读的文本报告。
你的任务是分析用户提供的对话历史，结合给定的世界观、角色设定与玩家背景，
生成一简短的剧情分析，帮助作者理解当前剧情状态并为后续创作提供参考。

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
请用流畅的中文段落输出，包含以下要点，每部分用空行隔开：
1. 剧情概览：用100字总结当前剧情走向。
2. 关键事件：按时间顺序列出1-5个最重要的事件，每条30字左右，用“·”开头。
3. 角色状态：分析主要角色与玩家的当前情感、立场变化。
4. 长期记忆：提炼1-5点对后续剧情有持续影响的伏笔或重要信息。
5. 冲突张力：指出当前存在的主要矛盾或悬念。

无需任何标题或前缀，直接输出正文即可。
"""

        messages = [
            {"role": "system", "content": structured_prompt},
            {"role": "user", "content": "请根据提供的对话历史和上下文信息，分析当前剧情情况，提取关键事件并整理长期记忆。"}
        ]

        response = client.chat.completions.create(
            model="glm-4-plus",
            messages=messages,
            thinking={"type": "enabled"},
            temperature=0.3
        )

        print("剧情分析原始响应：", response)
        analysis_text = response.choices[0].message.content
        print("剧情分析内容：", analysis_text)

        # 直接返回纯文本分析结果
        return jsonify({"analysis": analysis_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@llm_bp.route("/novel", methods=["POST"])
def generate_novel():
    try:
        # 获取前端传递的参数
        data = request.get_json()
        if not data or "prompt" not in data:
            return jsonify({"error": "缺少小说生成提示信息"}), 400

        # 新增：从请求体获取上下文字段并组装为第二条 system 消息
        # 构造结构化提示词，更聚焦于对话内容
        worldview = data.get("worldview")
        master_sitting = data.get("master_sitting")
        main_characters = data.get("main_characters")
        background = data.get("background")

        # 统一组装主要角色信息
        if isinstance(main_characters, (list, tuple)):
            mc_text = ", ".join([str(x) for x in main_characters])
        elif isinstance(main_characters, dict):
            mc_text = json.dumps(main_characters, ensure_ascii=False)
        else:
            mc_text = str(main_characters) if main_characters is not None else ""

        structured_prompt = f"""[Role]
你是一位资深小说家，擅长将对话内容扩展为精彩的小说故事。
你的创作重点应该是**忠实还原并扩展用户提供的对话内容**，将其转化为连贯、生动的小说叙述。

[创作指南]
1. **主要素材**：用户提供的对话内容是创作的核心和基础，必须完整保留其情节发展人物互动。
2. **辅助素材**：世界观、人物设定等信息仅作为辅助参考，用于确保风格一致，不应喧宾夺主。
3. **创作方式**：将对话自然地融入故事叙述中，适当补充场景描写和人物心理，使对话更具画面感。

[Context References]
# 世界观（仅供风格参考）
{worldview or "无特殊设定"}

# 核心人物设定
{master_sitting or "无特定人物关系"}

# 其余角色（必要时可出现）
{mc_text if main_characters else "无其他角色"}

# 玩家背景
{background or "无特定场景"}

[Output Requirements]
1. 第一段必须是章节标题，简洁有力，直接点明故事核心。
2. 主体内容必须**紧密围绕用户提供的对话内容**展开创作。
3. 语言风格需与世界观保持一致，自然流畅。
4. 无需任何开场白（如'好的，故事开始了'等引导语），直接以标题开始创作。
5. 详略得当：对话相关内容应详细展开，设定相关但与对话无关的内容可简要带过。
"""

        messages = [
            {"role": "system", "content": structured_prompt},
            {"role": "user", "content": f"请基于以下对话内容创作小说：\n{data['prompt']}"}
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
