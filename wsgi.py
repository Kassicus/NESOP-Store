from server import app
import os
import logging

# Ensure upload directory exists with proper permissions
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
except PermissionError:
    logging.error(f"Permission denied when creating directory: {app.config['UPLOAD_FOLDER']}")
    # Continue execution - the directory might already exist

if __name__ == "__main__":
    app.run()