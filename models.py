from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(64), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    avatar        = db.Column(db.String(200), default='')
    bio           = db.Column(db.String(300), default='')
    role          = db.Column(db.String(20), default='user')  # user / admin
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    is_active     = db.Column(db.Boolean, default=True)
    comments      = db.relationship('Comment', backref='author', lazy='dynamic')
    likes         = db.relationship('CommentLike', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username}>'


class Comment(db.Model):
    __tablename__ = 'comments'
    id         = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.String(255), nullable=False)  # NewsAPI article URL hash
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content    = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)
    parent_id  = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    replies    = db.relationship('Comment', backref=db.backref('parent', remote_side='Comment.id'), lazy='dynamic')
    likes      = db.relationship('CommentLike', backref='comment', lazy='dynamic')

    def like_count(self):
        return self.likes.count()

    def __repr__(self):
        return f'<Comment {self.id} by {self.user_id}>'


class CommentLike(db.Model):
    __tablename__ = 'comment_likes'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'comment_id'),)


class SavedArticle(db.Model):
    __tablename__ = 'saved_articles'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    article_id = db.Column(db.String(255), nullable=False)
    title      = db.Column(db.String(300))
    url        = db.Column(db.String(500))
    image      = db.Column(db.String(500))
    source     = db.Column(db.String(100))
    saved_at   = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'article_id'),)
