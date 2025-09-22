from flask import Flask, render_template, send_from_directory
from datetime import datetime
import os

app = Flask(__name__, template_folder='xxda', static_folder='xxda')

@app.route('/')
def index():
    # Sample data for the template
    data = {
        'gender': 'Male',  # 性别
        'student_id': '2021100123',  # 学号
        'school_name': 'Beijing University',  # 学校名称
        'degree_type': 'Bachelor',  # 学历类别
        'major': 'Computer Science',  # 专业名称
        'learning_format': 'Full-time',  # 学习形式
        'ethnicity': 'Han',  # 民族
        'id_number': '110***********1234',  # 证件号码
        'study_duration': '4',  # 学制
        'college': 'School of Computer Science',  # 学院
        'enrollment_date': '2021-09-01',  # 入学日期
        'expected_graduation_date': '2025-07-01',  # 预计毕业日期
        'admission_photo': './xxdap2_files/lqpic.do',  # 录取照片
    }
    return render_template('xxdap2.html', **data)

# Route to serve static files from xxdap2_files directory
@app.route('/xxdap2_files/<path:filename>')
def serve_static(filename):
    return send_from_directory('xxda/xxdap2_files', filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)