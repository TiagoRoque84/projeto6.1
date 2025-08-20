from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensions import db
from models import User
from utils import admin_required
# Importa a função para criptografar a senha
from werkzeug.security import generate_password_hash

admin_users_bp = Blueprint("admin_users", __name__, template_folder='../../templates/admin')

@admin_users_bp.route("/")
@login_required
@admin_required
def list():
    q = request.args.get("q","").strip()
    query = User.query
    if q:
        like = f"%{q}%"
        query = query.filter((User.username.ilike(like)) | (User.nome_completo.ilike(like)))
    items = query.order_by(User.username).all()
    return render_template("admin/users_list.html", items=items, q=q)

@admin_users_bp.route("/new", methods=["GET","POST"])
@login_required
@admin_required
def new():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","").strip()
        nome = request.form.get("nome_completo","").strip()
        role = request.form.get("role","user")
        active = bool(request.form.get("active"))
        if not username or not password:
            flash("Usuário e senha são obrigatórios.", "danger")
            return redirect(url_for("admin_users.new"))
        if User.query.filter_by(username=username).first():
            flash("Usuário já existe.", "danger")
            return redirect(url_for("admin_users.new"))
        
        # --- CORREÇÃO AQUI: Criptografa a senha antes de salvar ---
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        u = User(username=username, password=hashed_password, nome_completo=nome, role=role, active=active)
        
        db.session.add(u); db.session.commit()
        flash("Usuário criado.", "success")
        return redirect(url_for("admin_users.list"))
    return render_template("admin/user_form.html", title="Novo Usuário", item=None)

@admin_users_bp.route("/<int:uid>/edit", methods=["GET","POST"])
@login_required
@admin_required
def edit(uid):
    u = User.query.get_or_404(uid)
    if request.method == "POST":
        u.username = request.form.get("username", u.username).strip()
        
        # --- CORREÇÃO AQUI: Criptografa a nova senha, se for fornecida ---
        new_password = request.form.get("password")
        if new_password:
            u.password = generate_password_hash(new_password, method='pbkdf2:sha256')
            
        u.nome_completo = request.form.get("nome_completo", u.nome_completo).strip()
        u.role = request.form.get("role", u.role)
        u.active = bool(request.form.get("active"))
        db.session.commit()
        flash("Usuário atualizado.", "success")
        return redirect(url_for("admin_users.list"))
    return render_template("admin/user_form.html", title="Editar Usuário", item=u)