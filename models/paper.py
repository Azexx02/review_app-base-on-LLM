from datetime import datetime
from models import db

class Paper(db.Model):
    __tablename__ = 'papers'  # 对应数据库papers表

    id = db.Column(db.Integer, primary_key=True)
    paper_name = db.Column(db.String(100), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_ids = db.Column(db.Text, nullable=False)  # 存储逗号分隔的题目ID字符串
    total_score = db.Column(db.Integer, default=100)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    # 把题目ID字符串转为列表
    def get_question_ids(self):
        return list(map(int, self.question_ids.split(','))) if self.question_ids else []

    # 计算卷子总题数
    def get_question_count(self):
        return len(self.get_question_ids())

    def __repr__(self):
        return f'<Paper {self.id}: {self.paper_name}>'