from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from config import config
from models import db
from models.user import User
from models.question import Question
from models.wrong_question import WrongQuestion
from models.paper import Paper
from services.llm_service import generate_questions_from_material
from services.pdf_service import generate_paper_pdf, generate_wrong_pdf
import json
import os
import chardet

# 初始化Flask应用
app = Flask(__name__)
app.config.from_object(config['default'])  # 加载配置

# 初始化数据库
db.init_app(app)

# 初始化登录管理
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # 未登录时跳转的页面

# 加载用户（Flask-Login要求）
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 创建数据库表（首次运行时执行）
with app.app_context():
    db.create_all()  # 若已手动创建表，注释此行
    pass

# ---------------------- 首页路由 ----------------------
@app.route('/')
def index():
    return render_template('index.html', current_user=current_user)

# ---------------------- 用户相关路由 ----------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')

        # 验证用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在！')
            return redirect(url_for('register'))

        # 创建新用户
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('注册成功！请登录')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        # 验证密码
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('用户名或密码错误！')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ---------------------- 题目相关路由 ----------------------
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_material():
    if request.method == 'POST':
        # 接收用户上传的资料（文本或文件）
        material_text = request.form.get('material_text')  # 文本输入
        material_file = request.files.get('material_file')  # 文件上传

        # 处理资料内容
        material = ""
        if material_file and material_file.filename:
            # 读取文件内容（支持txt、md等文本文件）
            material = material_file.read().decode('utf-8')
        elif material_text:
            material = material_text

        if not material:
            flash('请输入或上传资料内容！')
            return redirect(url_for('upload_material'))

        # 调用LLM生成题目
        questions = generate_questions_from_material(material, question_count=10)
        if "error" in questions:
            flash(questions["error"])
            return redirect(url_for('upload_material'))

        # 保存题目到数据库
        for q in questions:
            new_question = Question(
                question_type=q['type'],
                content=q['content'],
                options=json.dumps(q['options']) if 'options' in q else None,
                correct_answer=q['correct_answer'],
                source_material=material[:500] + "..." if len(material) > 500 else material,  # 截取前500字
                creator_id=current_user.id
            )
            db.session.add(new_question)
        db.session.commit()

        flash(f'成功生成{len(questions)}道题目！')
        return redirect(url_for('question_list'))

    return render_template('upload.html')

@app.route('/questions')
@login_required
def question_list():
    # 筛选题目（支持按类型、评分排序）
    question_type = request.args.get('type', '')
    sort_by = request.args.get('sort', 'score_desc')  # 按评分降序

    query = Question.query
    if question_type:
        query = query.filter_by(question_type=question_type)

    # 排序
    if sort_by == 'score_desc':
        query = query.order_by(Question.score.desc())
    elif sort_by == 'create_time_desc':
        query = query.order_by(Question.create_time.desc())

    questions = query.all()
    return render_template('question_list.html', questions=questions, current_user=current_user)

@app.route('/question/score/<int:question_id>', methods=['POST'])
@login_required
def score_question(question_id):
    # 给题目评分
    question = Question.query.get_or_404(question_id)
    new_score = float(request.form.get('score'))
    if 1.0 <= new_score <= 5.0:
        question.update_score(new_score)
        flash('评分成功！')
    else:
        flash('评分必须在1-5分之间！')
    return redirect(url_for('question_list'))

# ---------------------- 卷子相关路由 ----------------------
@app.route('/paper/create', methods=['GET', 'POST'])
@login_required
def create_paper():
    if request.method == 'POST':
        paper_name = request.form.get('paper_name')
        question_ids = request.form.getlist('question_ids')  # 选中的题目ID列表

        if not paper_name or len(question_ids) == 0:
            flash('请输入卷子名称并选择题目！')
            return redirect(url_for('create_paper'))

        # 创建卷子
        new_paper = Paper(
            paper_name=paper_name,
            creator_id=current_user.id,
            question_ids=','.join(question_ids)
        )
        db.session.add(new_paper)
        db.session.commit()

        flash(f'卷子创建成功！共{len(question_ids)}道题')
        return redirect(url_for('paper_detail', paper_id=new_paper.id))

    # GET请求：加载所有题目供选择
    questions = Question.query.order_by(Question.score.desc()).all()
    return render_template('paper_create.html', questions=questions)

@app.route('/paper/<int:paper_id>')
@login_required
def paper_detail(paper_id):
    paper = Paper.query.get_or_404(paper_id)
    # 获取卷子对应的题目
    question_ids = paper.get_question_ids()
    questions = Question.query.filter(Question.id.in_(question_ids)).all()
    return render_template('paper_detail.html', paper=paper, questions=questions)

@app.route('/paper/do/<int:paper_id>')
@login_required
def do_paper(paper_id):
    paper = Paper.query.get_or_404(paper_id)
    question_ids = paper.get_question_ids()
    questions = Question.query.filter(Question.id.in_(question_ids)).all()
    return render_template('paper_do.html', paper=paper, questions=questions)

@app.route('/paper/submit/<int:paper_id>', methods=['POST'])
@login_required
def submit_paper(paper_id):
    paper = Paper.query.get_or_404(paper_id)
    question_ids = paper.get_question_ids()
    questions = Question.query.filter(Question.id.in_(question_ids)).all()
    correct_count = 0
    wrong_question_ids = []

    # 判分并记录错题
    for question in questions:
        user_answer = request.form.get(f'answer_{question.id}')
        if not user_answer:
            wrong_question_ids.append(question.id)
            continue

        # 验证答案（不同题型处理）
        if question.question_type == 'fill_blank':
            # 填空题：忽略空格和大小写（可根据需求调整）
            if user_answer.strip().lower() == question.correct_answer.strip().lower():
                correct_count += 1
            else:
                wrong_question_ids.append(question.id)
        elif question.question_type == 'single_choice':
            # 单选题：直接对比
            if user_answer == question.correct_answer:
                correct_count += 1
            else:
                wrong_question_ids.append(question.id)
        elif question.question_type == 'multiple_choice':
            # 多选题：按逗号分隔后排序对比
            user_ans_list = sorted(user_answer.split(','))
            correct_ans_list = sorted(question.correct_answer.split(','))
            if user_ans_list == correct_ans_list:
                correct_count += 1
            else:
                wrong_question_ids.append(question.id)

    # 记录错题到错题本
    for qid in wrong_question_ids:
        existing_wrong = WrongQuestion.query.filter_by(user_id=current_user.id, question_id=qid).first()
        if existing_wrong:
            existing_wrong.increment_count()  # 已有错题，增加次数
        else:
            new_wrong = WrongQuestion(user_id=current_user.id, question_id=qid)
            db.session.add(new_wrong)
    db.session.commit()

    # 计算得分
    total_questions = len(questions)
    score = int((correct_count / total_questions) * paper.total_score) if total_questions > 0 else 0
    flash(f'提交成功！得分：{score}/{paper.total_score} 分 | 正确{correct_count}道 | 错误{len(wrong_question_ids)}道')
    return redirect(url_for('paper_detail', paper_id=paper_id))

# ---------------------- 错题本与PDF导出路由 ----------------------
@app.route('/wrong')
@login_required
def wrong_list():
    # 查看个人错题本
    wrong_questions = WrongQuestion.query.filter_by(user_id=current_user.id).order_by(WrongQuestion.last_wrong_time.desc()).all()
    # 获取对应的题目信息
    question_ids = [wq.question_id for wq in wrong_questions]
    questions = Question.query.filter(Question.id.in_(question_ids)).all()
    # 映射错题与题目（保持顺序一致）
    question_map = {q.id: q for q in questions}
    wrong_with_questions = [(wq, question_map[wq.question_id]) for wq in wrong_questions]
    return render_template('wrong_list.html', wrong_with_questions=wrong_with_questions)

@app.route('/export/paper/<int:paper_id>')
@login_required
def export_paper(paper_id):
    # 导出卷子为PDF
    paper = Paper.query.get_or_404(paper_id)
    question_ids = paper.get_question_ids()
    questions = Question.query.filter(Question.id.in_(question_ids)).all()
    
    # 生成PDF临时文件
    pdf_path = f'/tmp/paper_{paper_id}_{current_user.id}.pdf'
    generate_paper_pdf(paper, questions, pdf_path)
    
    # 发送PDF文件给用户（自动删除临时文件）
    return send_file(pdf_path, as_attachment=True, download_name=f'{paper.paper_name}.pdf', mimetype='application/pdf')

@app.route('/export/wrong')
@login_required
def export_wrong():
    # 导出错题本为PDF
    wrong_questions = WrongQuestion.query.filter_by(user_id=current_user.id).all()
    if not wrong_questions:
        flash('没有错题可导出！')
        return redirect(url_for('wrong_list'))
    
    question_ids = [wq.question_id for wq in wrong_questions]
    questions = Question.query.filter(Question.id.in_(question_ids)).all()
    question_map = {q.id: q for q in questions}
    ordered_questions = [question_map[wq.question_id] for wq in wrong_questions]
    
    # 生成PDF临时文件
    pdf_path = f'/tmp/wrong_{current_user.id}.pdf'
    generate_wrong_pdf(current_user.id, wrong_questions, ordered_questions, pdf_path)
    
    return send_file(pdf_path, as_attachment=True, download_name=f'错题本_{current_user.username}.pdf', mimetype='application/pdf')