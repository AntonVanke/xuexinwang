"""
学籍信息管理系统 - 主应用
"""
import os
from flask import Flask, render_template, request, url_for, redirect

from config import Config
from models.student import Student
from utils.id_generator import IDGenerator


# 初始化Flask应用
app = Flask(__name__,
            static_folder='detail_files',  # 保持兼容性
            static_url_path='/detail_files',
            template_folder='templates')

# 加载配置
app.config.from_object(Config)
Config.init_dirs()


@app.route('/')
def index():
    """首页 - 表单页面"""
    # 默认使用带预览的新版本
    return render_template('form_with_preview.html')


@app.route('/form')
def form_simple():
    """简单表单页面（无预览）"""
    return render_template('form.html')


@app.route('/preview')
def form_preview():
    """带实时预览的表单页面"""
    return render_template('form_with_preview.html')


@app.route('/submit', methods=['POST'])
def submit():
    """提交表单数据"""
    if request.method == 'POST':
        # 收集表单数据
        form_data = {
            "photo": request.form.get('photo'),
            "name": request.form.get('name'),
            "sex": request.form.get('sex'),
            "date": request.form.get('date'),
            "school": request.form.get('school'),
            "level": request.form.get('level'),
            "major": request.form.get('major'),
            "rz": request.form.get('rz'),
            "detail": {
                "mz": request.form.get('mz'),
                "zjhm": request.form.get('zjhm'),
                "xz": request.form.get('xz'),
                "xljb": request.form.get('xljb'),
                "fy": request.form.get('fy'),
                "xs": request.form.get('xs'),
                "bj": request.form.get('bj'),
                "xh": request.form.get('xh'),
                "rxrq": request.form.get('rxrq'),
                "yjbyrq": request.form.get('yjbyrq'),
                "xjzt": request.form.get('xjzt')
            }
        }

        # 创建学生对象
        student = Student(form_data)

        # 生成唯一ID
        unique_id = IDGenerator.generate_unique_id(Config.DATA_DIR)

        # 保存数据到新位置
        student.save_to_file(os.path.join(Config.DATA_DIR, f"{unique_id}.json"))

        # 同时保存到旧位置以保持兼容性
        if not os.path.exists(Config.DETAIL_FILES_DIR):
            os.makedirs(Config.DETAIL_FILES_DIR)
        student.save_to_file(os.path.join(Config.DETAIL_FILES_DIR, f"{unique_id}.json"))

        # 构建完整的URL
        full_url = request.url_root.rstrip('/') + f'/student/{unique_id}'

        return render_template('success.html', url=full_url)

    return redirect(url_for('index'))


@app.route('/student/<student_id>')
def view_student(student_id):
    """查看学生详情页面"""
    try:
        # 优先从新位置读取
        file_path = os.path.join(Config.DATA_DIR, f"{student_id}.json")
        if not os.path.exists(file_path):
            # 尝试从旧位置读取
            file_path = os.path.join(Config.DETAIL_FILES_DIR, f"{student_id}.json")

        student = Student.from_json_file(file_path)
        return render_template('student_detail.html', data=student)
    except FileNotFoundError:
        return render_template('404.html'), 404
    except Exception as e:
        app.logger.error(f"Error loading student {student_id}: {e}")
        return render_template('error.html'), 500


# 兼容旧的URL路径
@app.route('/d/<short_url>')
def legacy_view(short_url):
    """兼容旧的查看链接"""
    return redirect(url_for('view_student', student_id=short_url))


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return render_template('error.html'), 500


if __name__ == '__main__':
    app.run(
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT
    )