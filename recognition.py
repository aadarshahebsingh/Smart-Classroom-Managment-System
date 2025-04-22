import os
import cv2
import numpy as np
import face_recognition
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class FaceRecognitionSystem:
    def __init__(self, app=None):
        self.app = app
        self.known_face_encodings = []
        self.known_face_ids = []
        
    def load_student_data(self, students):
        """Load face encoding data from student models"""
        self.known_face_encodings = []
        self.known_face_ids = []
        
        for student in students:
            encoding = student.get_face_encoding()
            if encoding is not None:
                self.known_face_encodings.append(encoding)
                self.known_face_ids.append(student.id)
                
        logger.debug(f"Loaded {len(self.known_face_encodings)} face encodings")
        return len(self.known_face_encodings)
    
    def process_and_save_student_photo(self, file_path):
        """Process a student's photo and extract face encoding"""
        try:
            # Load the image
            image = face_recognition.load_image_file(file_path)
            
            # Detect faces
            face_locations = face_recognition.face_locations(image)
            
            if not face_locations:
                logger.warning(f"No face found in {file_path}")
                return None
            
            # Get the encoding of the first face found
            face_encoding = face_recognition.face_encodings(image, face_locations)[0]
            return face_encoding
            
        except Exception as e:
            logger.error(f"Error processing student photo: {str(e)}")
            return None
    
    def recognize_from_frame(self, frame_data):
        """Recognize students from a camera frame"""
        try:
            # Convert frame data to numpy array
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Convert from BGR (OpenCV format) to RGB (face_recognition format)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Find all faces in the frame
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            matched_students = []
            
            for face_encoding in face_encodings:
                # Compare this face with known faces
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.6)
                
                # If there's a match
                if True in matches:
                    matched_index = matches.index(True)
                    student_id = self.known_face_ids[matched_index]
                    matched_students.append(student_id)
            
            return matched_students
            
        except Exception as e:
            logger.error(f"Error during face recognition: {str(e)}")
            return []
