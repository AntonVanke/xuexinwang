from flask import Flask, render_template, send_from_directory, request, redirect, url_for, jsonify
from datetime import datetime
import os
import sqlite3
import hashlib
import time
from werkzeug.utils import secure_filename
import re
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import qrcode
import json
import secrets

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
    """Generate a unique 16-digit hexadecimal query ID"""
    return secrets.token_hex(8)  # Generates 16 hex characters

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

def get_student_by_id_number(id_number):
    """Get student data by ID number"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM students WHERE id_number = ?", (id_number,))
    student = c.fetchone()
    conn.close()
    return student

@app.route('/check_id_number', methods=['POST'])
def check_id_number():
    """Check if an ID number already exists in the database"""
    id_number = request.json.get('id_number')
    if not id_number:
        return jsonify({'exists': False})

    existing_student = get_student_by_id_number(id_number)
    if existing_student:
        return jsonify({
            'exists': True,
            'name': existing_student['name'],
            'query_id': existing_student['query_id'],
            'view_url': url_for('view', query_id=existing_student['query_id'], _external=True)
        })
    return jsonify({'exists': False})

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

    # Check if this is an update or new submission
    force_update = request.form.get('force_update') == 'true'

    # Check for existing student with same ID number
    existing_student = get_student_by_id_number(id_number)

    if existing_student and not force_update:
        # ID exists but user hasn't confirmed update
        return jsonify({
            'error': 'duplicate',
            'message': f"身份证号已存在，学生姓名：{existing_student['name']}",
            'existing_query_id': existing_student['query_id'],
            'view_url': url_for('view', query_id=existing_student['query_id'], _external=True)
        }), 409

    # Use existing query_id if updating, otherwise generate new one
    if existing_student and force_update:
        query_id = existing_student['query_id']
    else:
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
        if existing_student and force_update:
            # Update existing record
            c.execute('''UPDATE students SET
                         name = ?, gender = ?, ethnicity = ?, student_id = ?,
                         school_name = ?, college = ?, major = ?, degree_level = ?,
                         degree_type = ?, learning_format = ?, study_duration = ?,
                         enrollment_date = ?, expected_graduation_date = ?,
                         admission_photo = COALESCE(?, admission_photo)
                         WHERE id_number = ?''',
                      (request.form.get('name'),
                       request.form.get('gender'),
                       request.form.get('ethnicity'),
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
                       admission_photo,
                       id_number))
        else:
            # Insert new record
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

def mask_name(name):
    """Privacy protection for name - keep first and last character"""
    if len(name) <= 1:
        return name
    elif len(name) == 2:
        return name[0] + '*'
    else:
        return name[0] + '*' * (len(name) - 2) + name[-1]

@app.route('/generate_code/<query_id>')
def generate_code(query_id):
    """Generate user image collection code based on template"""
    student = get_student_by_query_id(query_id)
    if not student:
        return jsonify({'error': '学生信息不存在'}), 404

    try:
        # Load template image
        template_path = os.path.join('templates', 'txcjm.png')
        img = Image.open(template_path)
        draw = ImageDraw.Draw(img)

        # Try to use a Chinese font, fall back to default if not available
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/simsun.ttc", 20)
            font_small = ImageFont.truetype("C:/Windows/Fonts/simsun.ttc", 16)
        except:
            font = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Add student information to the image with privacy protection
        text_color = (51, 51, 51)

        # Add masked name
        masked_name = mask_name(student['name'])
        draw.text((100, 92), masked_name, fill=text_color, font=font)

        # Add ID number (only last 4 digits)
        id_number = student['id_number']
        masked_id = '*' * 14 + id_number[-4:]
        draw.text((100, 125), masked_id, fill=text_color, font=font)

        # Add school name
        draw.text((100, 158), student['school_name'], fill=text_color, font=font)

        # Add level
        draw.text((100, 191), student['degree_level'], fill=text_color, font=font)

        # Generate QR code data
        qr_data = {
            "sjc": str(int(time.time() * 1000)),  # Current timestamp in milliseconds
            "cjm": query_id,
            "yxdm": "10001",  # School code - you may want to make this configurable
            "zjhm": id_number[-4:],  # Last 4 digits of ID
            "xh": student['student_id'],
            "cc": "本科",
            "xllb": "本科",
            "fy": student['college'],  # College name
            "xm": masked_name,  # Masked name
            "bh": ""
        }

        # Convert to base64
        qr_content = base64.b64encode(json.dumps(qr_data, ensure_ascii=False).encode('utf-8')).decode('utf-8')

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=5,
            border=2,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Resize QR code to fit in the green box
        qr_size = 170  # Slightly smaller than green box to have padding
        qr_img = qr_img.resize((qr_size, qr_size))

        # Calculate position to center QR code in green box
        # Green box is approximately at (65, 260) with size 200x200
        green_box_x = 65
        green_box_y = 260
        green_box_size = 200

        # Calculate center position for QR code
        qr_x = green_box_x + (green_box_size - qr_size) // 2
        qr_y = green_box_y + (green_box_size - qr_size) // 2

        # Paste QR code onto the template centered in green box
        img.paste(qr_img, (qr_x, qr_y))

        # Convert image to base64
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{img_base64}'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

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