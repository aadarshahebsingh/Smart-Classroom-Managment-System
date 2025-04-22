from app import app, db
from models import User, Role, Class, Teacher, Student

# Create initial test users
def create_test_data():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        print("Creating test data...")
        
        # Create a class
        test_class = Class(name="Class 10-A", grade=10)
        db.session.add(test_class)
        db.session.flush()  # Get class ID
        
        # Create admin user
        admin = User(
            email="admin@school.edu",
            name="Admin User",
            role=Role.ADMIN
        )
        admin.set_password("admin123")
        db.session.add(admin)
        
        # Create teacher user
        teacher = User(
            email="teacher@school.edu",
            name="Teacher User",
            role=Role.TEACHER
        )
        teacher.set_password("teacher123")
        db.session.add(teacher)
        db.session.flush()  # Get teacher ID
        
        # Create teacher record
        teacher_record = Teacher(
            user_id=teacher.id,
            subject="Mathematics"
        )
        db.session.add(teacher_record)
        
        # Link teacher to class
        teacher_record.classes.append(test_class)
        
        # Create student user
        student = User(
            email="student@school.edu",
            name="Student User",
            role=Role.STUDENT
        )
        student.set_password("student123")
        db.session.add(student)
        db.session.flush()  # Get student ID
        
        # Create student record
        student_record = Student(
            user_id=student.id,
            class_id=test_class.id
        )
        db.session.add(student_record)
        
        # Commit all changes
        db.session.commit()
        
        print("Test data created successfully!")
        print("\nTest Users:")
        print(f"Admin: email=admin@school.edu, password=admin123")
        print(f"Teacher: email=teacher@school.edu, password=teacher123")
        print(f"Student: email=student@school.edu, password=student123")

if __name__ == "__main__":
    create_test_data()