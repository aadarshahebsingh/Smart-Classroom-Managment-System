import os
import logging
import random
from datetime import datetime
from PIL import Image
import io
import numpy as np
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleFaceRecognitionSystem:
    """
    A simplified face recognition system that doesn't require OpenCV or face_recognition libraries.
    This implementation simulates facial recognition by random matching from the pool of students.
    """
    def __init__(self, app=None):
        self.app = app
        self.known_student_ids = []
        self.student_photos = {}  # Store student photo paths
        self.last_recognized = set()  # Track recently recognized students to make it more realistic
        
    def load_student_data(self, students):
        """Load student data for recognition"""
        self.known_student_ids = []
        self.student_photos = {}
        
        for student in students:
            self.known_student_ids.append(student.id)
            if student.photo_path:
                self.student_photos[student.id] = student.photo_path
                
        logger.info(f"Loaded {len(self.known_student_ids)} students for recognition")
        return len(self.known_student_ids)
    
    def process_and_save_student_photo(self, file_path):
        """Process a student's photo"""
        try:
            # Just verify it's a valid image file
            img = Image.open(file_path)
            width, height = img.size
            
            # Generate a fake encoding that's deterministic based on the image
            # This will ensure the same student always gets the same encoding
            # but still allows us to simulate matching
            mock_encoding = []
            for i in range(128):  # Use 128 values like face_recognition does
                # Use a combination of image properties to generate the encoding
                val = (width * height + os.path.getsize(file_path) + i) % 100 / 100.0
                mock_encoding.append(val)
                
            logger.info(f"Processed photo with dimensions {width}x{height}: {file_path}")
            return mock_encoding
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return None
    
    def recognize_from_frame(self, frame_data):
        """Simulate recognizing students from a camera frame"""
        try:
            # Make sure we actually get an image
            try:
                Image.open(io.BytesIO(frame_data))
                logger.info("Valid image received for recognition")
            except Exception as e:
                logger.warning(f"Invalid image data: {e}")
                # Still continue the process even with invalid image
            
            recognized_students = []
            
            # Only proceed if we have students to recognize
            if not self.known_student_ids:
                logger.warning("No students loaded for recognition")
                return []
                
            # Add some randomness to make it more realistic
            if random.random() < 0.1:  # 10% chance of detecting no one
                logger.info("No faces detected in this frame")
                return []
                
            # Determine number of students to detect (1-3)
            num_to_detect = random.randint(1, min(3, len(self.known_student_ids)))
            
            # Get students that haven't been recognized recently
            available_students = set(self.known_student_ids) - self.last_recognized
            if not available_students:  # If all have been recognized recently, reset
                available_students = set(self.known_student_ids)
                self.last_recognized = set()
            
            # Select random students
            if available_students:
                selected_students = random.sample(list(available_students), min(num_to_detect, len(available_students)))
                recognized_students = selected_students
                
                # Update last recognized
                self.last_recognized.update(selected_students)
                logger.info(f"Recognized {len(recognized_students)} students")
            
            return recognized_students
            
        except Exception as e:
            logger.error(f"Error during face recognition: {str(e)}")
            return []
