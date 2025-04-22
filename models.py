from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

# User roles
class Role:
    ADMIN = 'admin'
    TEACHER = 'teacher'
    STUDENT = 'student'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Create relationships
    student_info = db.relationship('Student', backref='user', uselist=False, cascade="all, delete-orphan")
    teacher_info = db.relationship('Teacher', backref='user', uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == Role.ADMIN
    
    def is_teacher(self):
        return self.role == Role.TEACHER
    
    def is_student(self):
        return self.role == Role.STUDENT
    
    def __repr__(self):
        return f'<User {self.name} ({self.role})>'

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    photo_path = db.Column(db.String(255))
    face_encoding = db.Column(db.Text)  # Stored as JSON string
    
    # Relationships
    attendance_records = db.relationship('Attendance', backref='student', cascade="all, delete-orphan")
    
    def set_face_encoding(self, encoding):
        """Store face encoding as JSON string"""
        if encoding is not None:
            # Handle both numpy arrays and lists
            try:
                # For numpy arrays
                self.face_encoding = json.dumps(encoding.tolist())
            except AttributeError:
                # For regular lists
                self.face_encoding = json.dumps(encoding)
        else:
            self.face_encoding = None
    
    def get_face_encoding(self):
        """Get face encoding as numpy array"""
        if self.face_encoding:
            import numpy as np
            return np.array(json.loads(self.face_encoding))
        return None
    
    def __repr__(self):
        return f'<Student {self.user.name if self.user else "Unknown"}>'

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    
    # Many-to-many relationship with Class through association table
    classes = db.relationship('Class', secondary='teacher_class', backref='teachers')
    
    def __repr__(self):
        return f'<Teacher {self.user.name if self.user else "Unknown"} - {self.subject}>'

# Association table for Teacher-Class many-to-many relationship
teacher_class = db.Table('teacher_class',
    db.Column('teacher_id', db.Integer, db.ForeignKey('teacher.id'), primary_key=True),
    db.Column('class_id', db.Integer, db.ForeignKey('class.id'), primary_key=True)
)

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    grade = db.Column(db.Integer, nullable=False)  # Grade 1-12
    
    # Relationships
    students = db.relationship('Student', backref='class_group', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Class {self.name} - Grade {self.grade}>'

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    status = db.Column(db.String(20), nullable=False, default='present')  # present, absent, late
    method = db.Column(db.String(20), nullable=False)  # facial, manual
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    recorded_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # Teacher who recorded (if manual)
    
    # Relationship with recorder
    recorder = db.relationship('User', foreign_keys=[recorded_by])
    
    def __repr__(self):
        return f'<Attendance {self.student_id} - {self.date} - {self.status}>'
