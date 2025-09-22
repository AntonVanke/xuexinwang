"""
应用配置文件
"""
import os


class Config:
    """应用配置类"""

    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-please-change-in-production'
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

    # 服务器配置
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 48088))

    # 文件和目录配置
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    STATIC_DIR = os.path.join(BASE_DIR, 'static')
    TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

    # 旧的兼容性配置
    DETAIL_FILES_DIR = os.path.join(BASE_DIR, 'detail_files')

    # ID生成配置
    ID_LENGTH = 7
    ID_PREFIX = ""

    # 上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB最大上传大小
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    @classmethod
    def init_dirs(cls):
        """初始化必要的目录"""
        dirs = [cls.DATA_DIR, cls.STATIC_DIR, cls.DETAIL_FILES_DIR]
        for dir_path in dirs:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)