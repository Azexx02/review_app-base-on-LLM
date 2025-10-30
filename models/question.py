from datetime import datetime
from models import db
import json

class Question(db.Model):
    __tablename__ = 'questions'  # 对应数据库questions表

    id = db.Column(db.Integer, primary_key=True)
    question_type = db.Column(db.Enum('single_choice', 'multiple_choice', 'fill_blank'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text, nullable=True)  # 存储JSON字符串
    correct_answer = db.Column(db.Text, nullable=False)
    source_material = db.Column(db.Text, nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Numeric(2, 1), default=3.0)
    score_count = db.Column(db.Integer, default=1)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    # 把选项JSON字符串转为列表
    def get_options(self):
        if self.options:
            return json.loads(self.options)
        return []

    # 计算新的平均评分
    def update_score(self, new_score):
        total_score = self.score * self.score_count + new_score
        self.score_count += 1
        self.score = round(total_score / self.score_count, 1)
        db.session.commit()

    def __repr__(self):
        return f'<Question {self.id}: {self.content[:20]}...>'