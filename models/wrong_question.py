from datetime import datetime
from models import db

class WrongQuestion(db.Model):
    __tablename__ = 'wrong_questions'  # 对应数据库wrong_questions表

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    wrong_count = db.Column(db.Integer, default=1)
    last_wrong_time = db.Column(db.DateTime, default=datetime.utcnow)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    # 增加错题次数
    def increment_count(self):
        self.wrong_count += 1
        self.last_wrong_time = datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return f'<WrongQuestion user:{self.user_id} question:{self.question_id}>'