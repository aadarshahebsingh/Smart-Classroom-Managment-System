from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, FileField, HiddenField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from models import User, Role

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = HiddenField('Role', default=Role.TEACHER)
    submit = SubmitField('Login')

class StudentRegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    class_id = SelectField('Class', coerce=int, validators=[DataRequired()])
    photo = FileField('Student Photo (for facial recognition)')
    submit = SubmitField('Register Student')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please use a different email.')

class TeacherRegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=100)])
    classes = SelectField('Class', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Register Teacher')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please use a different email.')

class ClassForm(FlaskForm):
    name = StringField('Class Name', validators=[DataRequired(), Length(max=50)])
    grade = IntegerField('Grade (1-12)', validators=[DataRequired()])
    submit = SubmitField('Add Class')
    
    def validate_grade(self, grade):
        if grade.data < 1 or grade.data > 12:
            raise ValidationError('Grade must be between 1 and 12.')

class ManualAttendanceForm(FlaskForm):
    student_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('present', 'Present'), 
        ('absent', 'Absent'), 
        ('late', 'Late')
    ], validators=[DataRequired()])
    submit = SubmitField('Mark Attendance')
