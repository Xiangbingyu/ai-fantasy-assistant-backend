from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from typing import List, Optional

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

class WorldCharacter(db.Model):
    __tablename__ = 'world_characters'
    
    id = db.Column(db.Integer, primary_key=True)
    world_id = db.Column(db.Integer, db.ForeignKey('worlds.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    background = db.Column(db.Text)
    
    # 关系
    world = db.relationship('World', backref=db.backref('characters', lazy=True))

class World(db.Model):
    __tablename__ = 'worlds'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    tags = db.Column(db.ARRAY(db.String(50)))  # PostgreSQL数组类型
    is_public = db.Column(db.Boolean, default=False)
    worldview = db.Column(db.Text)
    master_setting = db.Column(db.Text)
    origin_world_id = db.Column(db.Integer, db.ForeignKey('worlds.id'), nullable=True)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    popularity = db.Column(db.Integer, default=0)
    
    # 关系
    creator = db.relationship('User', backref=db.backref('created_worlds', lazy=True))
    origin_world = db.relationship('World', remote_side=[id], backref='derived_worlds')

class Chapter(db.Model):
    __tablename__ = 'chapters'
    
    id = db.Column(db.Integer, primary_key=True)
    world_id = db.Column(db.Integer, db.ForeignKey('worlds.id'), nullable=False)
    creator_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    opening = db.Column(db.Text)
    background = db.Column(db.Text)
    is_default = db.Column(db.Boolean, default=False)
    origin_chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=True)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    world = db.relationship('World', backref=db.backref('chapters', lazy=True))
    creator = db.relationship('User', backref=db.backref('created_chapters', lazy=True))
    origin_chapter = db.relationship('Chapter', remote_side=[id], backref='derived_chapters')

class ConversationMessage(db.Model):
    __tablename__ = 'conversation_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.Enum('user', 'ai', name='message_role'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    chapter = db.relationship('Chapter', backref=db.backref('messages', lazy=True))
    user = db.relationship('User', backref=db.backref('messages', lazy=True))

class NovelRecord(db.Model):
    __tablename__ = 'novel_records'
    
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    popularity = db.Column(db.Integer, default=0)
    
    # 关系
    chapter = db.relationship('Chapter', backref=db.backref('novels', lazy=True))
    user = db.relationship('User', backref=db.backref('novels', lazy=True))

class UserWorld(db.Model):
    __tablename__ = 'user_worlds'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    world_id = db.Column(db.Integer, db.ForeignKey('worlds.id'), nullable=False)
    role = db.Column(db.Enum('creator', 'participant', 'viewer', name='user_role'), nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    user = db.relationship('User', backref=db.backref('user_worlds', lazy=True))
    world = db.relationship('World', backref=db.backref('user_roles', lazy=True))
    
    # 联合唯一约束
    __table_args__ = (
        db.UniqueConstraint('user_id', 'world_id', name='unique_user_world'),
    )