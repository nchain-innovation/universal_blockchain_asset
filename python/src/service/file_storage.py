import os
import uuid
from fastapi import UploadFile
from werkzeug.utils import secure_filename

class FileStorage:
    def __init__(self, storage_dir: str = "../data/images", allowed_extensions: set = {"png", "jpg", "jpeg", "gif"}):
        self.storage_dir = storage_dir
        self.allowed_extensions = allowed_extensions
        self.file_data = {}  # Dictionary to store UUID, username, and file_path
        os.makedirs(self.storage_dir, exist_ok=True)  # Ensure the storage directory exists
    
    def allowed_file(self, filename: str) -> bool:
        """Check if the file type is allowed."""
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions    

    #  ----------------------------------------------------------------
    def save_file(self, file_content: bytes, filename: str, username: str) -> str:
        """Save an uploaded file to disk, and store its metadata."""
        # Ensure the filename is safe to use on any OS
        safe_filename = secure_filename(filename)

        # Check if the file is allowed
        if not self.allowed_file(safe_filename):
            raise ValueError("File type is not allowed")

        # Generate a unique identifier (UUID) for the file
        unique_reference = str(uuid.uuid4())

        # Create the full file path
        file_path = os.path.join(self.storage_dir, f"{unique_reference}_{safe_filename}")

        # Write the file content to disk
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Store the UUID, username, and file path in the dictionary
        self.file_data[unique_reference] = {
            "username": username,
            "file_path": file_path
        }

        return unique_reference  # Return the unique reference for later access

    #  ----------------------------------------------------------------
    def get_file_data(self, unique_reference: str, username: str) -> str:
        """Retrieve the stored image file path for a given UUID and username."""
        file_info = self.file_data.get(unique_reference)
        if file_info:
            if file_info['username'] == username:
                file_path = file_info['file_path']
                if os.path.exists(file_path):
                    original_filename = file_path.split('_', 1)[1]  # Extract the original filename
                    return {"file_path": file_path, "filename": original_filename}
                else:
                    print(f"File not found: {file_path}")
                    raise ValueError("File not found on disk")
            else:
                print(f"Username does not match: {username}")
                raise ValueError("Username does not match")
        else:
            print(f"Asset_id not found: {unique_reference}")
            raise ValueError("File not found")
    
