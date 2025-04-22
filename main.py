import os
import logging
from app import app
import routes  # Import routes to register them with the app

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Ensure upload directory exists
os.makedirs(os.path.join('static', 'uploads'), exist_ok=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
