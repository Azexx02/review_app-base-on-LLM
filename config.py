import os
from dotenv import load_dotenv

load_dotenv()  # 加载环境变量

class Config:
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret_key_123')  # 生产环境需改为随机字符串
    DEBUG = os.getenv('DEBUG', 'True') == 'True'  # 开发环境True，生产环境False

    # MySQL数据库配置（替换为你的服务器MySQL信息）
    # 从环境变量读取MySQL连接信息
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT', '3306')}/{os.getenv('MYSQL_DB')}?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # LLM配置（二选一：API调用或本地部署）
    # 选项1：调用LLM API
    LLM_API_TYPE = "deepseek"  # 可改为"openai"、"tongyi"等（目前不支持）
    LLM_API_KEY = os.getenv("LLM_API_KEY")  
    LLM_API_BASE = "https://api.deepseek.com/v1"
    LLM_MODEL = "deepseek-chat"  # 模型名称

    # 本地部署LLM，需要可以去除注释，但是未测试
    # LLM_API_TYPE = "local"
    # LLM_MODEL_PATH = "/path/to/local/llama-3"  # 本地模型路径

# 开发环境配置
class DevelopmentConfig(Config):
    DEBUG = True

# 生产环境配置
class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24))  # 生产环境用随机密钥

# 选择配置（开发时用DevelopmentConfig，部署时改ProductionConfig）
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}