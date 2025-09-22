from flask import Flask, render_template, send_from_directory, request, redirect, url_for
from datetime import datetime
import os
import sqlite3
import hashlib
import time
from werkzeug.utils import secure_filename
import re

app = Flask(__name__, template_folder='.', static_folder='xxda')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['DATABASE'] = 'students.db'

# Create uploads directory if it doesn't exist
if not os.path.exists('uploads'):
    os.makedirs('uploads')

def init_db():
    """Initialize the database with students table"""
    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  query_id TEXT UNIQUE NOT NULL,
                  name TEXT NOT NULL,
                  gender TEXT NOT NULL,
                  ethnicity TEXT NOT NULL,
                  id_number TEXT NOT NULL,
                  student_id TEXT NOT NULL,
                  school_name TEXT NOT NULL,
                  college TEXT NOT NULL,
                  major TEXT NOT NULL,
                  degree_level TEXT NOT NULL,
                  degree_type TEXT NOT NULL,
                  learning_format TEXT NOT NULL,
                  study_duration TEXT NOT NULL,
                  enrollment_date TEXT NOT NULL,
                  expected_graduation_date TEXT NOT NULL,
                  admission_photo TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def generate_query_id():
    """Generate a unique query ID for each submission"""
    timestamp = str(time.time())
    hash_object = hashlib.md5(timestamp.encode())
    return hash_object.hexdigest()[:10]

def validate_id_number(id_number):
    """Validate Chinese ID number format"""
    # Basic validation: 18 digits with last one possibly being X
    pattern = r'^\d{17}[\dXx]$'
    if not re.match(pattern, id_number):
        return False

    # Validate checksum
    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']

    sum_val = sum(int(id_number[i]) * weights[i] for i in range(17))
    check_code = check_codes[sum_val % 11]

    return check_code == id_number[-1].upper()

def get_student_by_query_id(query_id):
    """Get student data by query ID"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM students WHERE query_id = ?", (query_id,))
    student = c.fetchone()
    conn.close()
    return student

@app.route('/')
def home():
    return render_template('templates/input_form.html')

@app.route('/view/<query_id>')
def view(query_id):
    student = get_student_by_query_id(query_id)
    if not student:
        return "学生信息不存在", 404

    # Convert Row to dict for template
    data = dict(student)
    # Map database fields to template variables
    data['gender'] = data['gender']
    data['student_id'] = data['student_id']
    data['school_name'] = data['school_name']
    data['degree_type'] = data['degree_level']  # Using degree_level for the badge
    data['major'] = data['major']
    data['learning_format'] = data['learning_format']
    data['ethnicity'] = data['ethnicity']
    data['id_number'] = data['id_number']
    data['study_duration'] = data['study_duration']
    data['college'] = data['college']
    data['enrollment_date'] = data['enrollment_date']
    data['expected_graduation_date'] = data['expected_graduation_date']
    data['admission_photo'] = data.get('admission_photo', './xxdap2_files/lqpic.do')

    return render_template('xxda/xxdap2.html', **data)

@app.route('/submit', methods=['POST'])
def submit():
    # Validate ID number
    id_number = request.form.get('id_number')
    if not validate_id_number(id_number):
        return "身份证号码格式不正确", 400

    # Generate unique query ID
    query_id = generate_query_id()

    # Handle file upload
    admission_photo = None
    if 'admission_photo' in request.files:
        file = request.files['admission_photo']
        if file and file.filename:
            filename = secure_filename(f"{query_id}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            admission_photo = f'/uploads/{filename}'

    # Save to database
    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()

    try:
        c.execute('''INSERT INTO students
                     (query_id, name, gender, ethnicity, id_number, student_id,
                      school_name, college, major, degree_level, degree_type,
                      learning_format, study_duration, enrollment_date,
                      expected_graduation_date, admission_photo)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (query_id,
                   request.form.get('name'),
                   request.form.get('gender'),
                   request.form.get('ethnicity'),
                   id_number,
                   request.form.get('student_id'),
                   request.form.get('school_name'),
                   request.form.get('college'),
                   request.form.get('major'),
                   request.form.get('degree_level'),
                   request.form.get('degree_type'),
                   request.form.get('learning_format'),
                   request.form.get('study_duration'),
                   request.form.get('enrollment_date'),
                   request.form.get('expected_graduation_date'),
                   admission_photo))
        conn.commit()
        conn.close()

        return redirect(url_for('success', query_id=query_id))
    except Exception as e:
        conn.close()
        return f"保存失败: {str(e)}", 500

@app.route('/success')
def success():
    query_id = request.args.get('query_id')
    if not query_id:
        return redirect(url_for('home'))

    student = get_student_by_query_id(query_id)
    if not student:
        return "学生信息不存在", 404

    return render_template('templates/success.html', data=dict(student), query_id=query_id)

# Route to serve static files from xxdap2_files directory
@app.route('/xxdap2_files/<path:filename>')
def serve_static(filename):
    return send_from_directory('xxda/xxdap2_files', filename)

# Route to serve uploaded files
@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory('uploads', filename)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)