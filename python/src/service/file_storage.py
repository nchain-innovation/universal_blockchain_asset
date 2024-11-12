import os
import uuid
from werkzeug.utils import secure_filename
import hashlib


class FileStorage:
    def __init__(self, allowed_extensions: set = {"png", "jpg", "jpeg", "gif"}):
        self.storage_dir = "/app/data/images" if os.environ.get("APP_ENV") == "docker" else "../data/images"

        self.allowed_extensions = allowed_extensions
        os.makedirs(self.storage_dir, exist_ok=True)     # Ensure the storage directory exists

    def allowed_file(self, filename: str) -> bool:
        """Check if the file type is allowed."""
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

    #  ----------------------------------------------------------------
    def save_file(self, file_content: bytes, filename: str) -> dict:
        """Save an uploaded file to disk, and store its metadata."""
        try:
            # Ensure the filename is safe to use on any OS
            safe_filename = secure_filename(filename)

            # Check if the file is allowed
            if not self.allowed_file(safe_filename):
                raise ValueError("File type is not allowed")

            # Generate a unique identifier (UUID) for the file
            unique_reference = str(uuid.uuid4())

            # Create the full file path
            tmp_filename = f"{unique_reference}_{safe_filename}"
            file_path = os.path.join(self.storage_dir, tmp_filename)

            # Write the file content to disk
            with open(file_path, "wb") as f:
                f.write(file_content)

            # Calculate the hash of the file content
            file_hash = hashlib.sha256(file_content).hexdigest()

            # return unique_reference  # Return the unique reference for later access
            return {"asset_id": unique_reference, "file_hash": file_hash, "filename": tmp_filename}

        except Exception as e:
            # Handle any exceptions that occur during the file saving process
            print(f"Error saving file: {str(e)}")
            return {"error": str(e)}

    #  ----------------------------------------------------------------
    def get_file_path(self, filename: str) -> str:
        """Retrieve the stored image file path and original filename for a given UUID and username.
        Returns:
            dict: A dictionary containing the file path and original filename.
        """
        file_path = os.path.join(self.storage_dir, f"{filename}")

        if os.path.exists(file_path):
            return file_path
        else:
            print(f"File not found: {file_path}")
            raise ValueError("File not found in storage")
