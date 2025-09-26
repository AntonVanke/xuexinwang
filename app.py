from flask import Flask, render_template, send_from_directory, request, redirect, url_for, jsonify, session
from datetime import datetime, timedelta
import os
import sqlite3
import hashlib
import time
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import re
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import qrcode
import json
import secrets
from functools import wraps

app = Flask(__name__, template_folder='.', static_folder='xxda')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
app.config['DATABASE'] = 'students.db'
app.config['SECRET_KEY'] = secrets.token_hex(32)  # For session management
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # Session expires after 2 hours

# Create uploads directory if it doesn't exist
if not os.path.exists('uploads'):
    os.makedirs('uploads')

def init_db():
    """Initialize the database with students and deleted_students tables"""
    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()

    # Create students table
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

    # Create deleted_students table (for soft delete)
    c.execute('''CREATE TABLE IF NOT EXISTS deleted_students
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  query_id TEXT NOT NULL,
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
                  created_at TIMESTAMP,
                  deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # Create admin table
    c.execute('''CREATE TABLE IF NOT EXISTS admin
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL DEFAULT 'admin',
                  password_hash TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  last_login TIMESTAMP)''')

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

def admin_required(f):
    """Decorator to require admin login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def check_admin_exists():
    """Check if admin account exists"""
    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM admin")
    count = c.fetchone()[0]
    conn.close()
    return count > 0

def create_admin(password):
    """Create admin account with password"""
    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()
    password_hash = generate_password_hash(password)
    try:
        c.execute("INSERT INTO admin (username, password_hash) VALUES ('admin', ?)", (password_hash,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def verify_admin_password(password):
    """Verify admin password"""
    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()
    c.execute("SELECT password_hash FROM admin WHERE username = 'admin'")
    result = c.fetchone()
    conn.close()
    if result:
        return check_password_hash(result[0], password)
    return False

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
        return render_template('templates/404.html', query_id=query_id), 404

    # Convert Row to dict for template
    data = dict(student)
    data['name'] = data['name']
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
            # Check file size (5MB limit)
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)  # Reset file pointer

            if file_size > 5 * 1024 * 1024:  # 5MB
                return jsonify({
                    'error': 'file_too_large',
                    'message': '文件大小超过5MB限制'
                }), 413

            # Generate filename: query_id-[8 random hex chars].extension
            original_filename = secure_filename(file.filename) if file.filename else 'photo'
            file_ext = os.path.splitext(original_filename)[1].lower()

            # If no extension or invalid extension, determine from file content
            if not file_ext or file_ext not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                # Read first few bytes to determine file type
                file.seek(0)
                header = file.read(12)
                file.seek(0)

                # Detect file type from magic bytes
                if header[:3] == b'\xff\xd8\xff':
                    file_ext = '.jpg'
                elif header[:8] == b'\x89PNG\r\n\x1a\n':
                    file_ext = '.png'
                elif header[:4] == b'GIF8':
                    file_ext = '.gif'
                elif header[:4] == b'RIFF' and header[8:12] == b'WEBP':
                    file_ext = '.webp'
                elif header[:2] == b'BM':
                    file_ext = '.bmp'
                else:
                    # Default to .jpg if cannot determine
                    file_ext = '.jpg'

            random_hex = secrets.token_hex(4)  # 8 hex characters
            filename = f"{query_id}-{random_hex}{file_ext}"
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

@app.route('/delete/<query_id>', methods=['POST'])
def delete_student(query_id):
    """Soft delete student by moving to deleted_students table"""
    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()

    try:
        # Get student data first
        c.execute("SELECT * FROM students WHERE query_id = ?", (query_id,))
        student = c.fetchone()

        if not student:
            conn.close()
            return jsonify({'success': False, 'message': '学生信息不存在'}), 404

        # Insert into deleted_students table
        c.execute('''INSERT INTO deleted_students
                     (query_id, name, gender, ethnicity, id_number, student_id,
                      school_name, college, major, degree_level, degree_type,
                      learning_format, study_duration, enrollment_date,
                      expected_graduation_date, admission_photo, created_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  student[1:])  # Skip the id field

        # Delete from students table
        c.execute("DELETE FROM students WHERE query_id = ?", (query_id,))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': '学生信息已删除'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

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

        # Resize QR code to fit in the green box (1.25x larger)
        qr_size = int(170 * 1.25)  # 212 pixels (1.25 times larger)
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
    # Ensure uploads directory exists
    uploads_dir = os.path.join(app.root_path, 'uploads')
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)

    file_path = os.path.join(uploads_dir, filename)

    # Check if file exists
    if not os.path.exists(file_path):
        # Return a placeholder image or 404
        return "File not found", 404

    # Determine MIME type from extension
    ext = os.path.splitext(filename)[1].lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp'
    }

    mimetype = mime_types.get(ext, 'application/octet-stream')

    return send_from_directory('uploads', filename, mimetype=mimetype)

# Route to serve placeholder image
@app.route('/temp/img_1.png')
def serve_placeholder():
    """Serve a minimal transparent 1x1 pixel PNG"""
    from flask import Response
    # Minimal transparent PNG (1x1 pixel)
    transparent_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05W\xcd\xca\x00\x00\x00\x00IEND\xaeB`\x82'
    return Response(transparent_png, mimetype='image/png')

# Admin routes
@app.route('/admin/login')
def admin_login():
    """Admin login page"""
    return render_template('templates/admin_login.html')

@app.route('/api/admin/check')
def admin_check():
    """Check if admin exists"""
    return jsonify({'exists': check_admin_exists()})

@app.route('/admin/setup', methods=['POST'])
def admin_setup():
    """Setup admin password for first time"""
    if check_admin_exists():
        return jsonify({'success': False, 'message': '管理员账户已存在'}), 400

    password = request.json.get('password')
    if not password or len(password) < 8:
        return jsonify({'success': False, 'message': '密码长度至少8位'}), 400

    if create_admin(password):
        session['admin_logged_in'] = True
        session.permanent = True
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': '创建管理员失败'}), 500

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    """Admin login authentication"""
    password = request.json.get('password')

    if verify_admin_password(password):
        session['admin_logged_in'] = True
        session.permanent = True

        # Update last login time
        conn = sqlite3.connect(app.config['DATABASE'])
        c = conn.cursor()
        c.execute("UPDATE admin SET last_login = CURRENT_TIMESTAMP WHERE username = 'admin'")
        conn.commit()
        conn.close()

        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': '密码错误'}), 401

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    return jsonify({'success': True})

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard page"""
    return render_template('templates/admin_dashboard.html')

@app.route('/api/admin/statistics')
@admin_required
def admin_statistics():
    """Get statistics for admin dashboard"""
    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()

    # Total students
    c.execute("SELECT COUNT(*) FROM students")
    total = c.fetchone()[0]

    # Today's additions
    c.execute("SELECT COUNT(*) FROM students WHERE DATE(created_at) = DATE('now', 'localtime')")
    today = c.fetchone()[0]

    # Deleted students
    c.execute("SELECT COUNT(*) FROM deleted_students")
    deleted = c.fetchone()[0]

    conn.close()

    return jsonify({
        'total': total,
        'today': today,
        'active': total,
        'deleted': deleted
    })

@app.route('/api/admin/students')
@admin_required
def admin_get_students():
    """Get paginated students list"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get total count
    c.execute("SELECT COUNT(*) FROM students")
    total = c.fetchone()[0]

    # Get paginated students
    offset = (page - 1) * per_page
    c.execute("SELECT * FROM students ORDER BY created_at DESC LIMIT ? OFFSET ?", (per_page, offset))
    students = [dict(row) for row in c.fetchall()]

    conn.close()

    return jsonify({
        'students': students,
        'page': page,
        'totalPages': (total + per_page - 1) // per_page,
        'total': total
    })

@app.route('/api/admin/students/search')
@admin_required
def admin_search_students():
    """Search students"""
    query = request.args.get('q', '')

    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    search_term = f'%{query}%'
    c.execute("""SELECT * FROM students
                 WHERE name LIKE ? OR id_number LIKE ? OR student_id LIKE ?
                 ORDER BY created_at DESC""",
              (search_term, search_term, search_term))

    students = [dict(row) for row in c.fetchall()]
    conn.close()

    return jsonify({'students': students})

@app.route('/api/admin/student/<query_id>')
@admin_required
def admin_get_student(query_id):
    """Get single student details"""
    student = get_student_by_query_id(query_id)
    if student:
        return jsonify(dict(student))
    else:
        return jsonify({'error': 'Student not found'}), 404

@app.route('/api/admin/student/<query_id>', methods=['PUT'])
@admin_required
def admin_update_student(query_id):
    """Update student information"""
    data = request.json

    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()

    try:
        c.execute("""UPDATE students SET
                     name = ?, gender = ?, ethnicity = ?, id_number = ?,
                     student_id = ?, school_name = ?, college = ?, major = ?,
                     degree_level = ?, degree_type = ?, learning_format = ?,
                     study_duration = ?, enrollment_date = ?, expected_graduation_date = ?
                     WHERE query_id = ?""",
                  (data['name'], data['gender'], data['ethnicity'], data['id_number'],
                   data['student_id'], data['school_name'], data['college'], data['major'],
                   data['degree_level'], data['degree_type'], data['learning_format'],
                   data['study_duration'], data['enrollment_date'], data['expected_graduation_date'],
                   query_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/student', methods=['POST'])
@admin_required
def admin_add_student():
    """Add new student"""
    data = request.json
    query_id = generate_query_id()

    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()

    try:
        c.execute("""INSERT INTO students
                     (query_id, name, gender, ethnicity, id_number, student_id,
                      school_name, college, major, degree_level, degree_type,
                      learning_format, study_duration, enrollment_date,
                      expected_graduation_date)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (query_id, data['name'], data['gender'], data['ethnicity'],
                   data['id_number'], data['student_id'], data['school_name'],
                   data['college'], data['major'], data['degree_level'],
                   data['degree_type'], data['learning_format'],
                   data['study_duration'], data['enrollment_date'],
                   data['expected_graduation_date']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'query_id': query_id})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/student/<query_id>', methods=['DELETE'])
@admin_required
def admin_delete_student(query_id):
    """Delete student (soft delete)"""
    return delete_student(query_id)

@app.route('/api/admin/export')
@admin_required
def admin_export():
    """Export all students data as CSV"""
    import csv
    from flask import Response

    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM students ORDER BY created_at DESC")
    students = c.fetchall()
    conn.close()

    def generate():
        # CSV header
        yield ','.join(['姓名', '性别', '身份证号', '学号', '学校', '学院', '专业', '学历', '入学日期', '毕业日期']) + '\n'

        # CSV data
        for student in students:
            row = [
                student['name'],
                student['gender'],
                student['id_number'],
                student['student_id'],
                student['school_name'],
                student['college'],
                student['major'],
                student['degree_level'],
                student['enrollment_date'],
                student['expected_graduation_date']
            ]
            yield ','.join(row) + '\n'

    return Response(generate(), mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=students.csv"})

if __name__ == '__main__':
    init_db()
    # host='0.0.0.0' 允许外网访问
    # 生产环境建议使用 debug=False
    app.run(host='0.0.0.0', debug=True, port=5000)