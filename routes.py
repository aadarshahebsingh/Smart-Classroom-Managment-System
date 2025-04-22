import os
import io
import base64
import logging
from datetime import datetime, date, timedelta
from functools import wraps

from flask import render_template, redirect, url_for, flash, request, jsonify, session, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from app import app, db
from models import User, Student, Teacher, Class, Attendance, Role
from forms import LoginForm, StudentRegistrationForm, TeacherRegistrationForm, ClassForm, ManualAttendanceForm
from recognition import SimpleFaceRecognitionSystem

# Initialize simple facial recognition system
face_recognition_system = SimpleFaceRecognitionSystem(app)

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Logger setup
logger = logging.getLogger(__name__)

# Role-based access control decorators
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('You need administrator privileges to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or (not current_user.is_teacher() and not current_user.is_admin()):
            flash('You need teacher privileges to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_student():
            flash('You need student privileges to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Utility functions
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin_dashboard'))
        elif current_user.is_teacher():
            return redirect(url_for('teacher_dashboard'))
        elif current_user.is_student():
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    
    # Handle role selection
    role = request.args.get('role', Role.TEACHER)
    if role in [Role.ADMIN, Role.TEACHER, Role.STUDENT]:
        form.role.data = role
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data) and user.role == form.role.data:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Login failed. Please check your email, password and role.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Admin routes
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    # Get summary data
    student_count = Student.query.count()
    teacher_count = Teacher.query.count()
    class_count = Class.query.count()
    
    # Get attendance statistics for the last 7 days
    today = date.today()
    week_ago = today - timedelta(days=7)
    attendance_data = db.session.query(
        Attendance.date, 
        db.func.count(Attendance.id),
        db.func.sum(db.case((Attendance.status == 'present', 1), else_=0))
    ).filter(Attendance.date >= week_ago).group_by(Attendance.date).all()
    
    dates = []
    counts = []
    present_counts = []
    
    for day in range(7):
        current_date = week_ago + timedelta(days=day)
        dates.append(current_date.strftime("%Y-%m-%d"))
        
        # Find if we have data for this date
        day_data = next((item for item in attendance_data if item[0] == current_date), None)
        if day_data:
            counts.append(day_data[1])
            present_counts.append(day_data[2] or 0)
        else:
            counts.append(0)
            present_counts.append(0)
    
    return render_template('admin/dashboard.html', 
                          student_count=student_count,
                          teacher_count=teacher_count,
                          class_count=class_count,
                          dates=dates,
                          counts=counts,
                          present_counts=present_counts,
                          now=datetime.now())

@app.route('/admin/students', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_students():
    form = StudentRegistrationForm()
    
    # Populate class dropdown
    form.class_id.choices = [(c.id, f"{c.name} (Grade {c.grade})") for c in Class.query.order_by(Class.grade).all()]
    
    if form.validate_on_submit():
        # Create user
        user = User(
            name=form.name.data,
            email=form.email.data,
            role=Role.STUDENT
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # Get user ID before creating student record
        
        # Process photo if uploaded
        photo_path = None
        face_encoding = None
        if form.photo.data:
            photo = form.photo.data
            if allowed_file(photo.filename):
                filename = secure_filename(f"student_{user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                photo.save(photo_path)
                
                # Process photo for facial recognition
                face_encoding = face_recognition_system.process_and_save_student_photo(photo_path)
                if face_encoding is None:
                    flash('Warning: No face detected in the photo. Facial recognition may not work.', 'warning')
        
        # Create student record
        student = Student(
            user_id=user.id,
            class_id=form.class_id.data,
            photo_path=photo_path
        )
        
        if face_encoding is not None:
            student.set_face_encoding(face_encoding)
        
        db.session.add(student)
        db.session.commit()
        
        flash(f'Student {form.name.data} has been registered successfully!', 'success')
        return redirect(url_for('manage_students'))
    
    # Get all students for the listing
    students = Student.query.join(User).join(Class).order_by(Class.grade, User.name).all()
    
    return render_template('admin/students.html', form=form, students=students)

@app.route('/admin/teachers', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_teachers():
    form = TeacherRegistrationForm()
    
    # Populate class dropdown
    form.classes.choices = [(c.id, f"{c.name} (Grade {c.grade})") for c in Class.query.order_by(Class.grade).all()]
    
    if form.validate_on_submit():
        # Create user
        user = User(
            name=form.name.data,
            email=form.email.data,
            role=Role.TEACHER
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # Get user ID before creating teacher record
        
        # Create teacher record
        teacher = Teacher(
            user_id=user.id,
            subject=form.subject.data
        )
        db.session.add(teacher)
        
        # Add class assignment
        class_obj = Class.query.get(form.classes.data)
        if class_obj:
            teacher.classes.append(class_obj)
        
        db.session.commit()
        
        flash(f'Teacher {form.name.data} has been registered successfully!', 'success')
        return redirect(url_for('manage_teachers'))
    
    # Get all teachers for the listing
    teachers = Teacher.query.join(User).order_by(User.name).all()
    
    return render_template('admin/teachers.html', form=form, teachers=teachers)

@app.route('/admin/classes', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_classes():
    form = ClassForm()
    
    if form.validate_on_submit():
        class_obj = Class(
            name=form.name.data,
            grade=form.grade.data
        )
        db.session.add(class_obj)
        db.session.commit()
        
        flash(f'Class {form.name.data} (Grade {form.grade.data}) has been added successfully!', 'success')
        return redirect(url_for('manage_classes'))
    
    # Get all classes for the listing
    classes = Class.query.order_by(Class.grade, Class.name).all()
    
    return render_template('admin/classroom.html', form=form, classes=classes)

@app.route('/admin/reports')
@login_required
@admin_required
def admin_reports():
    # Get attendance data grouped by class
    class_attendance = db.session.query(
        Class.name, 
        Class.grade,
        db.func.count(Student.id).label('student_count'),
        db.func.count(Attendance.id).label('attendance_count'),
        db.func.sum(db.case((Attendance.status == 'present', 1), else_=0)).label('present_count')
    ).select_from(Class).outerjoin(Student).outerjoin(
        Attendance, (Student.id == Attendance.student_id) & 
        (Attendance.date == date.today())
    ).group_by(Class.id).order_by(Class.grade).all()
    
    # Calculate attendance percentage
    class_stats = []
    for cls in class_attendance:
        if cls.student_count > 0:
            present_percent = (cls.present_count or 0) / cls.student_count * 100 if cls.student_count else 0
        else:
            present_percent = 0
            
        class_stats.append({
            'name': cls.name,
            'grade': cls.grade,
            'student_count': cls.student_count,
            'present_count': cls.present_count or 0,
            'present_percent': round(present_percent, 1)
        })
    
    # Get recognition method statistics
    method_stats = db.session.query(
        Attendance.method,
        db.func.count(Attendance.id).label('count')
    ).group_by(Attendance.method).all()
    
    method_counts = {method: count for method, count in method_stats}
    facial_count = method_counts.get('facial', 0)
    manual_count = method_counts.get('manual', 0)
    total_count = facial_count + manual_count
    
    recognition_stats = {
        'facial_count': facial_count,
        'manual_count': manual_count,
        'facial_percent': round((facial_count / total_count * 100) if total_count else 0, 1),
        'manual_percent': round((manual_count / total_count * 100) if total_count else 0, 1)
    }
    
    return render_template('admin/reports.html', 
                           class_stats=class_stats,
                           recognition_stats=recognition_stats,
                           now=datetime.now())

# Teacher routes
@app.route('/teacher/dashboard')
@login_required
@teacher_required
def teacher_dashboard():
    if current_user.is_admin():
        # Admin viewing teacher dashboard
        return render_template('teacher/dashboard.html', is_admin=True)
    
    # Get teacher info
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('login'))
    
    # Get classes taught by this teacher
    classes = teacher.classes
    
    # Get recent attendance for these classes
    class_ids = [cls.id for cls in classes]
    recent_attendance = Attendance.query.join(Student).filter(
        Student.class_id.in_(class_ids),
        Attendance.date >= (date.today() - timedelta(days=7))
    ).order_by(Attendance.timestamp.desc()).limit(10).all()
    
    return render_template('teacher/dashboard.html', 
                           teacher=teacher,
                           classes=classes,
                           recent_attendance=recent_attendance,
                           now=datetime.now())

@app.route('/teacher/attendance', methods=['GET', 'POST'])
@login_required
@teacher_required
def teacher_attendance():
    # Get teacher's classes
    if current_user.is_admin():
        # Admin can see all classes
        classes = Class.query.order_by(Class.grade, Class.name).all()
    else:
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        if not teacher:
            flash('Teacher profile not found.', 'danger')
            return redirect(url_for('teacher_dashboard'))
        classes = teacher.classes
    
    # Get selected class
    selected_class_id = request.args.get('class_id', type=int)
    if not selected_class_id and classes:
        selected_class_id = classes[0].id
    
    # Get students for the selected class
    students = []
    if selected_class_id:
        students = Student.query.filter_by(class_id=selected_class_id).join(User).order_by(User.name).all()
        
        # Load face encodings for recognition
        face_recognition_system.load_student_data(students)
    
    # Initialize the manual attendance form
    form = ManualAttendanceForm()
    form.student_id.choices = [(s.id, s.user.name) for s in students]
    
    if form.validate_on_submit():
        # Process manual attendance
        attendance = Attendance(
            student_id=form.student_id.data,
            status=form.status.data,
            method='manual',
            recorded_by=current_user.id
        )
        db.session.add(attendance)
        db.session.commit()
        
        flash('Attendance recorded successfully.', 'success')
        return redirect(url_for('teacher_attendance', class_id=selected_class_id))
    
    # Get today's attendance for these students
    today_attendance = {}
    if students:
        student_ids = [s.id for s in students]
        attendance_records = Attendance.query.filter(
            Attendance.student_id.in_(student_ids),
            Attendance.date == date.today()
        ).all()
        
        today_attendance = {record.student_id: record for record in attendance_records}
    
    return render_template('teacher/attendance.html',
                          classes=classes,
                          selected_class_id=selected_class_id,
                          students=students,
                          today_attendance=today_attendance,
                          form=form,
                          now=datetime.now())

@app.route('/api/recognize', methods=['POST'])
@login_required
@teacher_required
def recognize_students():
    try:
        # Get image data from request
        image_data = request.files.get('image')
        if not image_data:
            return jsonify({'success': False, 'message': 'No image data provided'})
        
        # Process the image to recognize students
        frame_data = image_data.read()
        matched_student_ids = face_recognition_system.recognize_from_frame(frame_data)
        
        if not matched_student_ids:
            return jsonify({'success': True, 'matched_students': []})
        
        # Get student details and mark attendance
        matched_students = []
        for student_id in matched_student_ids:
            student = Student.query.get(student_id)
            if student:
                # Check if attendance already marked today
                existing = Attendance.query.filter_by(
                    student_id=student.id,
                    date=date.today()
                ).first()
                
                if not existing:
                    # Mark attendance
                    attendance = Attendance(
                        student_id=student.id,
                        status='present',
                        method='facial',
                        recorded_by=current_user.id
                    )
                    db.session.add(attendance)
                    db.session.commit()
                
                # Add to matched students list
                matched_students.append({
                    'id': student.id,
                    'name': student.user.name,
                    'already_marked': existing is not None
                })
        
        return jsonify({'success': True, 'matched_students': matched_students})
    
    except Exception as e:
        logger.error(f"Error in facial recognition: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/teacher/reports')
@login_required
@teacher_required
def teacher_reports():
    # Get teacher's classes
    if current_user.is_admin():
        # Admin can see all classes
        classes = Class.query.order_by(Class.grade, Class.name).all()
    else:
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        if not teacher:
            flash('Teacher profile not found.', 'danger')
            return redirect(url_for('teacher_dashboard'))
        classes = teacher.classes
    
    # Get selected class
    selected_class_id = request.args.get('class_id', type=int)
    if not selected_class_id and classes:
        selected_class_id = classes[0].id
    
    # Get date range (default to current month)
    today = date.today()
    start_date = request.args.get('start_date', type=str)
    end_date = request.args.get('end_date', type=str)
    
    if not start_date:
        start_date = date(today.year, today.month, 1)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
    if not end_date:
        end_date = today
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get attendance data for the selected class and date range
    students = []
    attendance_data = {}
    
    if selected_class_id:
        students = Student.query.filter_by(class_id=selected_class_id).join(User).order_by(User.name).all()
        student_ids = [s.id for s in students]
        
        attendance_records = Attendance.query.filter(
            Attendance.student_id.in_(student_ids),
            Attendance.date >= start_date,
            Attendance.date <= end_date
        ).order_by(Attendance.date).all()
        
        # Organize attendance by student and date
        for record in attendance_records:
            if record.student_id not in attendance_data:
                attendance_data[record.student_id] = {}
            
            date_str = record.date.strftime('%Y-%m-%d')
            attendance_data[record.student_id][date_str] = record.status
    
    # Generate date range for the report
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    return render_template('teacher/reports.html',
                          classes=classes,
                          selected_class_id=selected_class_id,
                          start_date=start_date.strftime('%Y-%m-%d'),
                          end_date=end_date.strftime('%Y-%m-%d'),
                          students=students,
                          attendance_data=attendance_data,
                          date_range=date_range,
                          now=datetime.now())

# Student routes
@app.route('/student/dashboard')
@login_required
@student_required
def student_dashboard():
    # Get student info
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('login'))
    
    # Get attendance statistics
    total_days = db.session.query(db.func.count(db.func.distinct(Attendance.date))).scalar() or 0
    
    attendance_count = db.session.query(
        db.func.count(Attendance.id).label('total'),
        db.func.sum(db.case((Attendance.status == 'present', 1), else_=0)).label('present'),
        db.func.sum(db.case((Attendance.status == 'absent', 1), else_=0)).label('absent'),
        db.func.sum(db.case((Attendance.status == 'late', 1), else_=0)).label('late')
    ).filter(Attendance.student_id == student.id).first()
    
    stats = {
        'total_days': total_days,
        'days_present': attendance_count.present or 0,
        'days_absent': attendance_count.absent or 0,
        'days_late': attendance_count.late or 0,
        'attendance_rate': round(((attendance_count.present or 0) / total_days * 100) if total_days else 0, 1)
    }
    
    # Get recent attendance history
    recent_attendance = Attendance.query.filter_by(student_id=student.id).order_by(Attendance.date.desc()).limit(10).all()
    
    # Get attendance data for the last 30 days for the chart
    thirty_days_ago = date.today() - timedelta(days=30)
    attendance_by_day = db.session.query(
        Attendance.date,
        Attendance.status
    ).filter(
        Attendance.student_id == student.id,
        Attendance.date >= thirty_days_ago
    ).order_by(Attendance.date).all()
    
    # Format data for chart
    chart_dates = []
    chart_statuses = []
    
    for record in attendance_by_day:
        chart_dates.append(record.date.strftime('%Y-%m-%d'))
        chart_statuses.append(record.status)
    
    return render_template('student/dashboard.html',
                          student=student,
                          stats=stats,
                          recent_attendance=recent_attendance,
                          chart_dates=chart_dates,
                          chart_statuses=chart_statuses,
                          now=datetime.now())

# Static file routes
@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Student deletion route
@app.route('/admin/students/delete/<int:student_id>')
@login_required
@admin_required
def delete_student(student_id):
    # Find the student
    student = Student.query.get_or_404(student_id)
    
    # Get associated user
    user_id = student.user_id
    user = User.query.get(user_id)
    
    # Delete attendance records first to avoid foreign key constraint
    Attendance.query.filter_by(student_id=student.id).delete()
    
    # Delete student record
    db.session.delete(student)
    
    # Delete user if it exists
    if user:
        db.session.delete(user)
    
    # Commit changes
    db.session.commit()
    
    flash(f'Student and associated records have been deleted.', 'success')
    return redirect(url_for('manage_students'))
