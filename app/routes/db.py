from flask import Blueprint, request, jsonify
from app.models import db, World, Chapter, ConversationMessage, NovelRecord, UserWorld, WorldCharacter, User
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db_bp = Blueprint('db', __name__, url_prefix='/api/db')

# 1. 获取全部的World信息
@db_bp.route('/worlds', methods=['GET'])
def get_all_worlds():
    try:
        worlds = World.query.all()
        result = []
        for world in worlds:
            # 加载并返回世界角色
            characters = [
                {
                    'name': c.name,
                    'background': c.background
                } for c in world.characters
            ]
            result.append({
                'id': world.id,
                'user_id': world.user_id,
                'name': world.name,
                'tags': world.tags,
                'is_public': world.is_public,
                'worldview': world.worldview,
                'master_setting': world.master_setting,
                'origin_world_id': world.origin_world_id,
                'create_time': world.create_time.isoformat(),
                'popularity': world.popularity,
                'main_characters': characters
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 新增：按ID获取单个World详情（含角色）
@db_bp.route('/worlds/<int:world_id>', methods=['GET'])
def get_world_detail(world_id):
    try:
        world = World.query.get(world_id)
        if world is None:
            return jsonify({'error': '世界不存在'}), 404
        characters = [{'name': c.name, 'background': c.background} for c in world.characters]
        return jsonify({
            'id': world.id,
            'user_id': world.user_id,
            'name': world.name,
            'tags': world.tags,
            'is_public': world.is_public,
            'worldview': world.worldview,
            'master_setting': world.master_setting,
            'origin_world_id': world.origin_world_id,
            'create_time': world.create_time.isoformat(),
            'popularity': world.popularity,
            'main_characters': characters
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 2. 获取指定World和creator_user_id对应的全部Chapter信息
@db_bp.route('/worlds/<int:world_id>/chapters', methods=['GET'])
def get_chapters_by_world_and_creator(world_id):
    try:
        creator_user_id = request.args.get('creator_user_id', type=int)
        if not creator_user_id:
            # 如果没有提供creator_user_id，获取该世界下的所有章节
            chapters = Chapter.query.filter_by(world_id=world_id).all()
        else:
            # 如果提供了creator_user_id，按原逻辑过滤
            chapters = Chapter.query.filter_by(
                world_id=world_id,
                creator_user_id=creator_user_id
            ).all()
        
        result = [
            {
                'id': chapter.id,
                'world_id': chapter.world_id,
                'creator_user_id': chapter.creator_user_id,
                'name': chapter.name,
                'opening': chapter.opening,
                'background': chapter.background,
                'is_default': chapter.is_default,
                'origin_chapter_id': chapter.origin_chapter_id,
                'create_time': chapter.create_time.isoformat() if hasattr(chapter.create_time, 'isoformat') else chapter.create_time
            } for chapter in chapters
        ]
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 新增：按ID获取单个Chapter详情（供前端拉取background与world_id）
@db_bp.route('/chapters/<int:chapter_id>', methods=['GET'])
def get_chapter_detail(chapter_id):
    try:
        chapter = Chapter.query.get(chapter_id)
        if chapter is None:
            return jsonify({'error': '章节不存在'}), 404

        # 新增：加载所属世界并返回世界相关上下文字段
        world = World.query.get(chapter.world_id) if chapter.world_id else None

        return jsonify({
            'id': chapter.id,
            'world_id': chapter.world_id,
            'creator_user_id': chapter.creator_user_id,
            'name': chapter.name,
            'opening': chapter.opening,
            'background': chapter.background,
            'is_default': chapter.is_default,
            'origin_chapter_id': chapter.origin_chapter_id,
            'create_time': chapter.create_time.isoformat() if hasattr(chapter.create_time, 'isoformat') else chapter.create_time,
            # 新增字段（来自 World）
            'worldview': (world.worldview if world else None),
            # 前端使用 master_sitting，这里从 world.master_setting 做映射
            'master_sitting': (world.master_setting if world else None),
            'main_characters': ([{'name': c.name, 'background': c.background} for c in world.characters] if world else [])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 3. 获取指定chapter_id对应的全部ConversationMessage信息
@db_bp.route('/chapters/<int:chapter_id>/messages', methods=['GET'])
def get_messages_by_chapter(chapter_id):
    try:
        messages = ConversationMessage.query.filter_by(chapter_id=chapter_id).order_by(
            ConversationMessage.create_time
        ).all()
        
        result = [
            {
                'id': msg.id,
                'chapter_id': msg.chapter_id,
                'user_id': msg.user_id,
                'role': msg.role,
                'content': msg.content,
                'create_time': msg.create_time.isoformat()
            } for msg in messages
        ]
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 4. 获取指定chapter_id对应的全部NovelRecord信息
@db_bp.route('/chapters/<int:chapter_id>/novels', methods=['GET'])
def get_novels_by_chapter(chapter_id):
    try:
        novels = NovelRecord.query.filter_by(chapter_id=chapter_id).order_by(
            NovelRecord.create_time.desc()
        ).all()
        
        result = [
            {
                'id': novel.id,
                'chapter_id': novel.chapter_id,
                'user_id': novel.user_id,
                'title': novel.title,
                'content': novel.content,
                'create_time': novel.create_time.isoformat()
            } for novel in novels
        ]
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 新增：创建指定章节的NovelRecord
@db_bp.route('/chapters/<int:chapter_id>/novels', methods=['POST'])
def create_novel(chapter_id):
    try:
        data = request.get_json(silent=True) or request.form

        # 验证必填字段
        required_fields = ['user_id', 'content']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'缺少{field}参数'}), 400

        # 处理可选字段
        title = data.get('title')
        if 'create_time' in data:
            try:
                create_time = datetime.fromisoformat(data['create_time'])
            except Exception as ve:
                return jsonify({'error': f'时间格式错误: {str(ve)}'}), 400
        else:
            create_time = datetime.utcnow()

        # 构建NovelRecord对象
        novel = NovelRecord(
            chapter_id=chapter_id,
            user_id=data['user_id'],
            title=title,
            content=data['content'],
            create_time=create_time
        )

        db.session.add(novel)
        db.session.commit()

        # 返回创建的记录
        return jsonify({
            'id': novel.id,
            'chapter_id': novel.chapter_id,
            'user_id': novel.user_id,
            'title': novel.title,
            'content': novel.content,
            'create_time': novel.create_time.isoformat()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 5. 获取指定user_id和role对应的全部UserWorld信息
@db_bp.route('/user-worlds', methods=['GET'])
def get_user_worlds_by_user_and_role():
    try:
        user_id = request.args.get('user_id', type=int)
        role = request.args.get('role')
        
        if not user_id or not role:
            return jsonify({'error': '缺少user_id或role参数'}), 400
            
        if role not in ['creator', 'participant', 'viewer']:
            return jsonify({'error': '无效的role值'}), 400
            
        user_worlds = UserWorld.query.filter_by(
            user_id=user_id,
            role=role
        ).all()
        
        result = [
            {
                'id': uw.id,
                'user_id': uw.user_id,
                'world_id': uw.world_id,
                'role': uw.role,
                'create_time': uw.create_time.isoformat()
            } for uw in user_worlds
        ]
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 6. 注册或登录（POST）
@db_bp.route('/auth', methods=['POST'])
def register_or_login():
    try:
        data = request.get_json(silent=True) or request.form
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': '缺少username或password参数'}), 400

        user = User.query.filter_by(username=username).first()

        if user is None:
            hashed = generate_password_hash(password)
            user = User(username=username, password=hashed)
            db.session.add(user)
            db.session.commit()
            return jsonify({'user_id': user.id}), 201
        else:
            if check_password_hash(user.password, password):
                return jsonify({'user_id': user.id}), 200
            else:
                return jsonify({'error': '密码错误'}), 401
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@db_bp.route('/worlds', methods=['POST'])
def create_world():
    data = request.get_json(silent=True) or request.form
    world = World(
        user_id=data.get('user_id'),
        name=data.get('name'),
        tags=data.get('tags'),
        is_public=data.get('is_public'),
        worldview=data.get('worldview'),
        master_setting=data.get('master_setting'),
        origin_world_id=data.get('origin_world_id'),
        popularity=data.get('popularity'),
    )
    db.session.add(world)
    db.session.flush()

    characters = data.get('characters') or []
    if isinstance(characters, list):
        for ch in characters:
            wc = WorldCharacter(
                world_id=world.id,
                name=(ch.get('name') if isinstance(ch, dict) else None),
                background=(ch.get('background') if isinstance(ch, dict) else None)
            )
            db.session.add(wc)

    db.session.commit()
    return jsonify({
        'id': world.id,
        'user_id': world.user_id,
        'name': world.name,
        'tags': world.tags,
        'is_public': world.is_public,
        'worldview': world.worldview,
        'master_setting': world.master_setting,
        'main_characters': [
            {'name': c.name, 'background': c.background} for c in world.characters
        ],
        'origin_world_id': world.origin_world_id,
        'create_time': world.create_time.isoformat() if world.create_time else None,
        'popularity': world.popularity
    }), 201

@db_bp.route('/chapters', methods=['POST'])
def create_chapter():
    data = request.get_json(silent=True) or request.form
    chapter = Chapter(
        world_id=data.get('world_id'),
        creator_user_id=data.get('creator_user_id'),
        name=data.get('name'),
        opening=data.get('opening'),
        background=data.get('background'),
        is_default=data.get('is_default'),
        origin_chapter_id=data.get('origin_chapter_id'),
        create_time=data.get('create_time'),
    )
    db.session.add(chapter)
    db.session.commit()
    return jsonify({
        'id': chapter.id,
        'world_id': chapter.world_id,
        'creator_user_id': chapter.creator_user_id,
        'name': chapter.name,
        'opening': chapter.opening,
        'background': chapter.background,
        'is_default': chapter.is_default,
        'origin_chapter_id': chapter.origin_chapter_id,
        'create_time': chapter.create_time.isoformat() if hasattr(chapter.create_time, 'isoformat') else chapter.create_time
    }), 201

@db_bp.route('/chapters/<int:chapter_id>/messages', methods=['POST'])
def create_message(chapter_id):
    try:
        data = request.get_json(silent=True) or request.form
        
        # 验证必填字段
        required_fields = ['user_id', 'role', 'content']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'缺少{field}参数'}), 400
                
        # 验证role合法性
        if data['role'] not in ['user', 'ai']:
            return jsonify({'error': 'role必须为"user"或"ai"'}), 400

        # 构建消息对象
        message = ConversationMessage(
            chapter_id=chapter_id,
            user_id=data['user_id'],
            role=data['role'],
            content=data['content'],
            # 若未提供create_time则使用当前时间
            create_time=datetime.fromisoformat(data['create_time']) if 'create_time' in data else datetime.utcnow()
        )
        
        db.session.add(message)
        db.session.commit()
        
        # 返回创建的消息详情
        return jsonify({
            'id': message.id,
            'chapter_id': message.chapter_id,
            'user_id': message.user_id,
            'role': message.role,
            'content': message.content,
            'create_time': message.create_time.isoformat()
        }), 201
        
    except ValueError as ve:
        # 处理时间格式错误
        return jsonify({'error': f'时间格式错误: {str(ve)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 删除指定章节下大于等于指定ID的消息
@db_bp.route('/chapters/<int:chapter_id>/messages', methods=['DELETE'])
def delete_messages(chapter_id):
    try:
        # 获取请求参数（支持查询参数或JSON体）
        message_id = request.args.get('id', type=int)
        if not message_id:
            # 尝试从JSON体获取
            data = request.get_json(silent=True) or {}
            message_id = data.get('id', type=int)
        
        if not message_id:
            return jsonify({'error': '缺少id参数'}), 400
        
        # 查询并删除符合条件的消息（同章节且id >= 给定id）
        deleted_count = ConversationMessage.query.filter(
            ConversationMessage.chapter_id == chapter_id,
            ConversationMessage.id >= message_id
        ).delete(synchronize_session=False)
        
        db.session.commit()
        
        return jsonify({
            'message': f'成功删除{deleted_count}条消息',
            'deleted_count': deleted_count,
            'chapter_id': chapter_id,
            'target_id': message_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@db_bp.route('/chapters/<int:chapter_id>', methods=['DELETE'])
def delete_chapter(chapter_id):
    try:
        # 查找章节是否存在
        chapter = Chapter.query.get(chapter_id)
        if chapter is None:
            return jsonify({'error': '章节不存在'}), 404

        # 先删除该章节下的消息与小说（避免外键约束冲突）
        deleted_messages = ConversationMessage.query.filter(
            ConversationMessage.chapter_id == chapter_id
        ).delete(synchronize_session=False)
        deleted_novels = NovelRecord.query.filter(
            NovelRecord.chapter_id == chapter_id
        ).delete(synchronize_session=False)

        # 删除章节本身
        db.session.delete(chapter)
        db.session.commit()

        return jsonify({
            'message': '章节删除成功',
            'chapter_id': chapter_id,
            'deleted_messages': deleted_messages,
            'deleted_novels': deleted_novels
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@db_bp.route('/user-worlds', methods=['POST'])
def create_user_world():
    try:
        data = request.get_json(silent=True) or request.form
        user_id = data.get('user_id')
        world_id = data.get('world_id')
        role = data.get('role')
        create_time_str = data.get('create_time')

        # 基本校验
        if user_id is None or world_id is None or role is None:
            return jsonify({'error': '缺少user_id或world_id或role参数'}), 400
        if role not in ['creator', 'participant', 'viewer']:
            return jsonify({'error': '无效的role值'}), 400

        # 处理时间（可选）
        if create_time_str:
            try:
                create_time = datetime.fromisoformat(create_time_str)
            except Exception as ve:
                return jsonify({'error': f'时间格式错误: {str(ve)}'}), 400
        else:
            create_time = datetime.utcnow()

        # 创建关系
        uw = UserWorld(
            user_id=int(user_id),
            world_id=int(world_id),
            role=role,
            create_time=create_time
        )
        db.session.add(uw)
        db.session.commit()

        return jsonify({
            'id': uw.id,
            'user_id': uw.user_id,
            'world_id': uw.world_id,
            'role': uw.role,
            'create_time': uw.create_time.isoformat()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 删除世界及其所有相关数据
@db_bp.route('/worlds/<int:world_id>', methods=['DELETE'])
def delete_world(world_id):
    try:
        # 查找世界是否存在
        world = World.query.get(world_id)
        if world is None:
            return jsonify({'error': '世界不存在'}), 404

        # 1. 获取该世界下的所有章节ID
        chapters = Chapter.query.filter_by(world_id=world_id).all()
        chapter_ids = [chapter.id for chapter in chapters]
        
        # 2. 删除所有章节相关的消息和小说记录
        deleted_messages = 0
        deleted_novels = 0
        for chapter_id in chapter_ids:
            # 删除章节下的消息
            deleted_messages += ConversationMessage.query.filter(
                ConversationMessage.chapter_id == chapter_id
            ).delete(synchronize_session=False)
            
            # 删除章节下的小说
            deleted_novels += NovelRecord.query.filter(
                NovelRecord.chapter_id == chapter_id
            ).delete(synchronize_session=False)
        
        # 3. 删除所有章节
        deleted_chapters = Chapter.query.filter_by(world_id=world_id).delete(synchronize_session=False)
        
        # 4. 删除用户与世界的关系记录
        deleted_user_worlds = UserWorld.query.filter_by(world_id=world_id).delete(synchronize_session=False)
        
        # 5. 删除世界角色
        deleted_characters = WorldCharacter.query.filter_by(world_id=world_id).delete(synchronize_session=False)
        
        # 6. 最后删除世界本身
        db.session.delete(world)
        db.session.commit()

        return jsonify({
            'message': '世界删除成功',
            'world_id': world_id,
            'deleted_chapters': deleted_chapters,
            'deleted_messages': deleted_messages,
            'deleted_novels': deleted_novels,
            'deleted_user_worlds': deleted_user_worlds,
            'deleted_characters': deleted_characters
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500