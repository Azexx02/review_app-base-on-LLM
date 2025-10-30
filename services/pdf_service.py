from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
import os

# 注册中文字体
def register_font():
    try:
        
        font_path = os.path.join(os.path.dirname(__file__), "../static/font/SimHei.ttf")
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('SimHei', font_path))
        else:
            print("警告：未找到中文字体文件，PDF中文可能乱码")
    except Exception as e:
        print(f"字体注册失败：{str(e)}")

# 初始化字体
register_font()

def generate_paper_pdf(paper, questions, save_path):
    """
    生成卷子PDF
    :param paper: 卷子对象（Paper模型实例）
    :param questions: 题目列表（Question模型实例列表）
    :param save_path: PDF保存路径（如/tmp/paper_1.pdf）
    """
    doc = SimpleDocTemplate(save_path, pagesize=A4, rightMargin=inch/2, leftMargin=inch/2, topMargin=inch, bottomMargin=inch)
    elements = []
    styles = getSampleStyleSheet()
    styles['Heading1'].fontName = 'SimHei'  # 中文标题
    styles['Normal'].fontName = 'SimHei'   # 中文正文

    # 卷子标题
    elements.append(Paragraph(f"《{paper.paper_name}》", styles['Heading1']))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"总题数：{paper.get_question_count()} 道 | 总分：{paper.total_score} 分", styles['Normal']))
    elements.append(Spacer(1, 30))

    # 添加题目
    for idx, q in enumerate(questions, 1):
        # 题干
        elements.append(Paragraph(f"{idx}. 【{q.question_type.replace('_', ' ')}】{q.content}", styles['Normal']))
        # 选项（单选/多选）
        if q.question_type in ['single_choice', 'multiple_choice']:
            options = q.get_options()
            for opt in options:
                elements.append(Paragraph(f"   {opt}", styles['Normal']))
        # 正确答案（单独标注，方便复习）
        elements.append(Paragraph(f"   正确答案：{q.correct_answer}", styles['Normal']))
        elements.append(Spacer(1, 15))

    # 生成PDF
    doc.build(elements)
    return save_path

def generate_wrong_pdf(user_id, wrong_questions, questions, save_path):
    """
    生成错题本PDF
    :param user_id: 用户ID
    :param wrong_questions: 错题列表（WrongQuestion模型实例列表）
    :param questions: 对应题目列表（Question模型实例列表）
    :param save_path: PDF保存路径
    """
    doc = SimpleDocTemplate(save_path, pagesize=A4, rightMargin=inch/2, leftMargin=inch/2, topMargin=inch, bottomMargin=inch)
    elements = []
    styles = getSampleStyleSheet()
    styles['Heading1'].fontName = 'SimHei'
    styles['Normal'].fontName = 'SimHei'

    # 错题本标题
    elements.append(Paragraph("错题本", styles['Heading1']))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"用户ID：{user_id} | 错题总数：{len(wrong_questions)} 道", styles['Normal']))
    elements.append(Spacer(1, 30))

    # 添加错题
    for idx, (wq, q) in enumerate(zip(wrong_questions, questions), 1):
        elements.append(Paragraph(f"{idx}. 【{q.question_type.replace('_', ' ')}】{q.content}", styles['Normal']))
        if q.question_type in ['single_choice', 'multiple_choice']:
            for opt in q.get_options():
                elements.append(Paragraph(f"   {opt}", styles['Normal']))
        elements.append(Paragraph(f"   正确答案：{q.correct_answer}", styles['Normal']))
        elements.append(Paragraph(f"   做错次数：{wq.wrong_count} 次 | 最后做错时间：{wq.last_wrong_time.strftime('%Y-%m-%d')}", styles['Normal']))
        elements.append(Spacer(1, 15))

    doc.build(elements)
    return save_path