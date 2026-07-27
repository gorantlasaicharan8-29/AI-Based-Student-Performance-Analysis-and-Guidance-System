"""
utils/file_handler.py - Secure file upload and download utilities.
"""

import os
import uuid
from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "png", "jpg", "jpeg", "txt", "zip", "ppt", "pptx", "xlsx", "xls"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file, upload_folder: str, subfolder: str = "") -> tuple:
    """
    Save an uploaded file with a unique name.
    Returns (saved_filename, original_filename) or raises ValueError.
    """
    if not file or file.filename == "":
        raise ValueError("No file selected.")

    if not allowed_file(file.filename):
        raise ValueError(f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"

    save_dir = os.path.join(upload_folder, subfolder) if subfolder else upload_folder
    os.makedirs(save_dir, exist_ok=True)

    full_path = os.path.join(save_dir, unique_name)
    file.save(full_path)

    # Return relative path (subfolder/unique_name)
    relative_path = os.path.join(subfolder, unique_name) if subfolder else unique_name
    return relative_path, original_filename


def delete_file(upload_folder: str, relative_path: str):
    """Delete a file from the upload directory."""
    if not relative_path:
        return
    full_path = os.path.join(upload_folder, relative_path)
    if os.path.exists(full_path):
        os.remove(full_path)


def get_file_size_mb(upload_folder: str, relative_path: str) -> float:
    """Return file size in MB."""
    full_path = os.path.join(upload_folder, relative_path)
    if os.path.exists(full_path):
        return os.path.getsize(full_path) / (1024 * 1024)
    return 0.0
