import openai
from config import Config

# 初始化LLM客户端
if Config.LLM_API_TYPE == "deepseek":
    client = openai.OpenAI(
        api_key=Config.LLM_API_KEY,
        base_url=Config.LLM_API_BASE
    )
elif Config.LLM_API_TYPE == "openai":
    client = openai.OpenAI(
        api_key=Config.LLM_API_KEY,
        base_url=Config.LLM_API_BASE
    )
else:  # 本地LLM（需额外安装transformers、torch等）
    client = None

def generate_questions_from_material(material, question_count=10):
    """
    从用户上传的资料生成题目
    :param material: 用户上传的资料内容（字符串）
    :param question_count: 生成题目数量（默认10道）
    :return: 生成的题目列表（字典格式）
    """
    if not material or len(material) < 100:
        return {"error": "资料内容过短，无法生成题目"}

    # 构建LLM提示词
    prompt = f"""
    你是一个专业的题库生成助手，需要根据以下资料生成{question_count}道复习题，包含单选、多选、填空三种类型（比例约4:3:3）。
    资料内容：{material}
    要求：
    1. 题目必须基于资料内容，不能编造信息；
    2. 单选/多选题选项需合理，干扰项不能明显错误；
    3. 输出格式严格按照JSON，不允许任何额外文字（否则无法解析）：
    {{
        "questions": [
            {{
                "type": "single_choice/multiple_choice/fill_blank",
                "content": "题干内容",
                "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],  // 填空类型无此键
                "correct_answer": "A"  // 单选填字母，多选填多个字母用逗号分隔（如"A,C"），填空填具体答案
            }}
        ]
    }}
    """

    try:
        # 调用LLM API生成题目
        response = client.chat.completions.create(
            model=Config.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,  # 控制随机性，0.7适中
            timeout=30
        )

        # 解析LLM返回的JSON结果
        import json5
        raw_content = response.choices[0].message.content.strip()
        result = json5.loads(raw_content)
        questions = result.get("questions", [])
        return questions

    except Exception as e:  
        print(f"LLM生成题目失败：{str(e)}")
        return {"error": f"生成失败：{str(e)}"}


# 本地LLM调用示例（若不用API，取消注释并安装依赖：transformers、torch、accelerate）
# def generate_questions_local(material, question_count=10):
#     from transformers import AutoTokenizer, AutoModelForCausalLM
#     tokenizer = AutoTokenizer.from_pretrained("your-local-llm-path")  # 本地LLM路径
#     model = AutoModelForCausalLM.from_pretrained("your-local-llm-path", device_map="auto")
#     prompt = f"（同上文prompt）"
#     inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
#     outputs = model.generate(**inputs, max_new_tokens=2000, temperature=0.7)
#     result = tokenizer.decode(outputs[0], skip_special_tokens=True)
#     import json5
#     return json5.loads(result).get("questions", [])