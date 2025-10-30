from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from models import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'  # 对应数据库users表

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 密码加密存储
    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256')

    # 验证密码
    def check_password(self, password):
        return check_password_hash(self.password, password)

    # 定义__repr__方法，方便调试
    def __repr__(self):
        return f'<User {self.username}>'