import os
from flask import Blueprint, current_app, send_from_directory
from flask_login import login_required

uploads_bp = Blueprint("uploads", __name__)

@uploads_bp.route("/uploads/<path:filename>")
@login_required
def serve_upload(filename):
    filename = filename.replace("\\", "/").lstrip("/")
    if filename.startswith("uploads/"):
        filename = filename[len("uploads/"):]
    root = os.path.join(
        current_app.root_path,
        current_app.config.get("UPLOAD_FOLDER", "uploads"),
    )
    return send_from_directory(root, filename, as_attachment=False)
