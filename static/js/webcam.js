/**
 * Webcam handling for facial recognition attendance
 */

const WebcamHandler = {
    video: null,
    canvas: null,
    stream: null,
    captureInterval: null,
    isCapturing: false,
    recognitionInProgress: false,
    captureDelay: 3000,  // Time between captures in ms
    
    /**
     * Initialize webcam
     */
    init: function() {
        this.video = document.getElementById('webcam');
        this.canvas = document.getElementById('capture-canvas');
        
        if (!this.video || !this.canvas) {
            console.error('Webcam elements not found');
            return false;
        }
        
        return true;
    },
    
    /**
     * Start webcam stream
     */
    start: async function() {
        try {
            if (!this.init()) return;
            
            // Request camera access
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: false
            });
            
            // Set video source to camera stream
            this.video.srcObject = this.stream;
            this.video.play();
            
            const startBtn = document.getElementById('start-webcam');
            const stopBtn = document.getElementById('stop-webcam');
            
            if (startBtn) startBtn.disabled = true;
            if (stopBtn) stopBtn.disabled = false;
            
            // Update status message
            this.updateStatus('Webcam started', 'success');
            
            return true;
        } catch (err) {
            console.error("Error accessing webcam:", err);
            this.updateStatus('Error accessing webcam: ' + err.message, 'danger');
            return false;
        }
    },
    
    /**
     * Stop webcam stream
     */
    stop: function() {
        if (this.stream) {
            // Stop all tracks in the stream
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
            
            // Clear video source
            if (this.video) {
                this.video.srcObject = null;
            }
            
            const startBtn = document.getElementById('start-webcam');
            const stopBtn = document.getElementById('stop-webcam');
            
            if (startBtn) startBtn.disabled = false;
            if (stopBtn) stopBtn.disabled = true;
            
            // Update status message
            this.updateStatus('Webcam stopped', 'info');
        }
        
        // Stop automatic captures
        this.stopCapturing();
    },
    
    /**
     * Start automatic capture loop
     */
    startCapturing: function() {
        if (!this.stream) {
            this.updateStatus('Please start the webcam first', 'warning');
            return;
        }
        
        if (this.isCapturing) return;
        
        this.isCapturing = true;
        
        const captureBtn = document.getElementById('start-capture');
        const stopCaptureBtn = document.getElementById('stop-capture');
        
        if (captureBtn) captureBtn.disabled = true;
        if (stopCaptureBtn) stopCaptureBtn.disabled = false;
        
        this.updateStatus('Started automatic face recognition', 'success');
        
        // Perform initial capture
        this.captureAndRecognize();
        
        // Set up interval for subsequent captures
        this.captureInterval = setInterval(() => {
            this.captureAndRecognize();
        }, this.captureDelay);
    },
    
    /**
     * Stop automatic capture loop
     */
    stopCapturing: function() {
        if (this.captureInterval) {
            clearInterval(this.captureInterval);
            this.captureInterval = null;
        }
        
        this.isCapturing = false;
        
        const captureBtn = document.getElementById('start-capture');
        const stopCaptureBtn = document.getElementById('stop-capture');
        
        if (captureBtn) captureBtn.disabled = false;
        if (stopCaptureBtn) stopCaptureBtn.disabled = true;
        
        this.updateStatus('Stopped automatic face recognition', 'info');
    },
    
    /**
     * Capture a frame and send for recognition
     */
    captureAndRecognize: function() {
        if (!this.stream || this.recognitionInProgress) return;
        
        try {
            this.recognitionInProgress = true;
            
            // Draw video frame to canvas
            const context = this.canvas.getContext('2d');
            this.canvas.width = this.video.videoWidth;
            this.canvas.height = this.video.videoHeight;
            context.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
            
            // Convert canvas to blob
            this.canvas.toBlob((blob) => {
                if (!blob) {
                    console.error('Failed to convert canvas to blob');
                    this.recognitionInProgress = false;
                    return;
                }
                
                // Create form data with the image blob
                const formData = new FormData();
                formData.append('image', blob, 'capture.jpg');
                
                // Send to server for recognition
                fetch('/api/recognize', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    this.handleRecognitionResult(data);
                })
                .catch(error => {
                    console.error('Error during recognition:', error);
                    this.updateStatus('Recognition error: ' + error.message, 'danger');
                })
                .finally(() => {
                    this.recognitionInProgress = false;
                });
            }, 'image/jpeg', 0.95);
            
        } catch (err) {
            console.error('Error capturing image:', err);
            this.recognitionInProgress = false;
        }
    },
    
    /**
     * Handle recognition results from the server
     */
    handleRecognitionResult: function(data) {
        if (!data.success) {
            this.updateStatus('Recognition failed: ' + (data.message || 'Unknown error'), 'danger');
            return;
        }
        
        const matchedStudents = data.matched_students || [];
        
        if (matchedStudents.length === 0) {
            this.updateStatus('No students recognized', 'warning');
            return;
        }
        
        // Update attendance status in UI
        matchedStudents.forEach(student => {
            const statusElement = document.getElementById(`attendance-status-${student.id}`);
            if (statusElement) {
                statusElement.textContent = 'Present';
                statusElement.className = 'badge badge-success';
            }
            
            const rowElement = document.getElementById(`student-row-${student.id}`);
            if (rowElement) {
                rowElement.classList.add('table-success');
            }
        });
        
        // Show recognition results
        const studentNames = matchedStudents.map(s => s.name).join(', ');
        this.updateStatus(`Recognized: ${studentNames}`, 'success');
        
        // Update the recognized students list
        this.updateRecognizedList(matchedStudents);
    },
    
    /**
     * Update the status message
     */
    updateStatus: function(message, type = 'info') {
        const statusElement = document.getElementById('webcam-status');
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `alert alert-${type}`;
        }
    },
    
    /**
     * Update recognized students list
     */
    updateRecognizedList: function(students) {
        const listElement = document.getElementById('recognized-students');
        if (!listElement) return;
        
        // Add new students to the list
        students.forEach(student => {
            // Check if student is already in the list
            const existingItem = listElement.querySelector(`[data-student-id="${student.id}"]`);
            if (!existingItem) {
                const listItem = document.createElement('li');
                listItem.className = 'list-group-item';
                listItem.setAttribute('data-student-id', student.id);
                listItem.textContent = student.name;
                
                if (student.already_marked) {
                    listItem.innerHTML += ' <span class="badge badge-info">Already marked</span>';
                } else {
                    listItem.innerHTML += ' <span class="badge badge-success">New</span>';
                }
                
                listElement.appendChild(listItem);
            }
        });
    }
};

// Set up event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const startWebcamBtn = document.getElementById('start-webcam');
    const stopWebcamBtn = document.getElementById('stop-webcam');
    const startCaptureBtn = document.getElementById('start-capture');
    const stopCaptureBtn = document.getElementById('stop-capture');
    const singleCaptureBtn = document.getElementById('single-capture');
    
    if (startWebcamBtn) {
        startWebcamBtn.addEventListener('click', () => WebcamHandler.start());
    }
    
    if (stopWebcamBtn) {
        stopWebcamBtn.addEventListener('click', () => WebcamHandler.stop());
        stopWebcamBtn.disabled = true;
    }
    
    if (startCaptureBtn) {
        startCaptureBtn.addEventListener('click', () => WebcamHandler.startCapturing());
    }
    
    if (stopCaptureBtn) {
        stopCaptureBtn.addEventListener('click', () => WebcamHandler.stopCapturing());
        stopCaptureBtn.disabled = true;
    }
    
    if (singleCaptureBtn) {
        singleCaptureBtn.addEventListener('click', () => WebcamHandler.captureAndRecognize());
    }
});
