import sys
import os
import logging

# Add the project directory to the Python path
sys.path.insert(0, '/var/www/thesuchows/nesop')

# Import the Flask app
from server import app as application

# Ensure upload directory exists with proper permissions
try:
    os.makedirs(application.config['UPLOAD_FOLDER'], exist_ok=True)
except PermissionError:
    logging.error(f"Permission denied when creating directory: {application.config['UPLOAD_FOLDER']}")
    # Continue execution - the directory might already exist