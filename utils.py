import os
import uuid
from functools import wraps

from flask import current_app, abort, redirect, url_for, flash
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

# Extensões permitidas p/ upload
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

def _allowed(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS or ext == ""

def save_file(storage, subdir: str):
    """
    Salva o arquivo em <root>/uploads/<subdir>/<arquivo>
    Retorna o caminho relativo a /uploads: ex.: 'func_docs/xxxx_arquivo.pdf'
    """
    if not storage or not storage.filename:
        return None

    safe = secure_filename(storage.filename)
    prefix = uuid.uuid4().hex[:8]
    name, ext = os.path.splitext(safe)
    filename = f"{prefix}_{name}{ext}"

    abs_dir = os.path.join(current_app.root_path, "uploads", subdir)
    os.makedirs(abs_dir, exist_ok=True)

    abs_path = os.path.join(abs_dir, filename)
    storage.save(abs_path)

    # caminho que sua rota /uploads/<path> entende
    return f"{subdir}/{filename}".replace("\\", "/")

def admin_required(fn):
    """
    Decorator para rotas administrativas.
    Exige usuário autenticado e com role 'admin'.
    """
    @wraps(fn)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if getattr(current_user, "role", None) != "admin":
            flash("Acesso restrito a administradores.", "danger")
            # Se preferir redirecionar pra home, troque por:
            # return redirect(url_for("main.index"))
            return abort(403)
        return fn(*args, **kwargs)
    return wrapper
