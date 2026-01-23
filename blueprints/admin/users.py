from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from flask_login import login_required
from extensions import db
from models import User
from utils import admin_required
from werkzeug.security import generate_password_hash

admin_users_bp = Blueprint("admin_users", __name__, template_folder='../../templates/admin')

@admin_users_bp.route("/")
@login_required
@admin_required
def list():
    q = request.args.get("q","").strip()
    query = User.query
    
    # CORREÇÃO CRÍTICA: Filtrar apenas usuários do tenant atual
    if hasattr(g, 'tenant') and g.tenant:
        query = query.filter_by(tenant_id=g.tenant.id)
    
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
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        u = User(username=username, password=hashed_password, nome_completo=nome, role=role, active=active)
        
        # CORREÇÃO CRÍTICA: Atribuir tenant_id automaticamente
        if hasattr(g, 'tenant') and g.tenant:
            u.tenant_id = g.tenant.id
        
        # Processar permissões para usuários normais
        if role == 'user':
            from permissions import AVAILABLE_PERMISSIONS
            permissions = {}
            for perm_code in AVAILABLE_PERMISSIONS.keys():
                perm_field = f'perm_{perm_code}'
                permissions[perm_code] = perm_field in request.form
            u.set_permissions(permissions)
        
        db.session.add(u)
        db.session.commit()
        flash("Usuário criado.", "success")
        return redirect(url_for("admin_users.list"))
    
    # Importar permissões
    from permissions import AVAILABLE_PERMISSIONS, DEFAULT_USER_PERMISSIONS
    return render_template("admin/user_form.html", 
                         title="Novo Usuário", 
                         item=None,
                         permissions=AVAILABLE_PERMISSIONS,
                         user_permissions=DEFAULT_USER_PERMISSIONS)

@admin_users_bp.route("/<int:uid>/edit", methods=["GET","POST"])
@login_required
@admin_required
def edit(uid):
    query = User.query.filter_by(id=uid)
    
    # CORREÇÃO CRÍTICA: Garantir que só pode editar usuários do próprio tenant
    if hasattr(g, 'tenant') and g.tenant:
        query = query.filter_by(tenant_id=g.tenant.id)
    
    u = query.first_or_404()
    
    if request.method == "POST":
        u.username = request.form.get("username", u.username).strip()
        
        new_password = request.form.get("password")
        if new_password:
            u.password = generate_password_hash(new_password, method='pbkdf2:sha256')
            
        u.nome_completo = request.form.get("nome_completo", u.nome_completo).strip()
        u.role = request.form.get("role", u.role)
        u.active = bool(request.form.get("active"))
        
        # Processar permissões para usuários normais
        if u.role == 'user':
            from permissions import AVAILABLE_PERMISSIONS
            permissions = {}
            for perm_code in AVAILABLE_PERMISSIONS.keys():
                perm_field = f'perm_{perm_code}'
                permissions[perm_code] = perm_field in request.form
            u.set_permissions(permissions)
        
        db.session.commit()
        flash("Usuário atualizado.", "success")
        return redirect(url_for("admin_users.list"))
    
    # GET - Importar permissões
    from permissions import AVAILABLE_PERMISSIONS
    return render_template("admin/user_form.html", 
                         title="Editar Usuário", 
                         item=u,
                         permissions=AVAILABLE_PERMISSIONS,
                         user_permissions=u.get_permissions_dict())

@admin_users_bp.route("/<int:uid>/delete", methods=["POST"])
@login_required  
@admin_required
def delete(uid):
    query = User.query.filter_by(id=uid)
    if hasattr(g, 'tenant') and g.tenant:
        query = query.filter_by(tenant_id=g.tenant.id)
    u = query.first_or_404()
    db.session.delete(u)
    db.session.commit()
    flash("Usuário excluído.", "success")
    return redirect(url_for("admin_users.list"))