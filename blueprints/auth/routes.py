# blueprints/auth/routes.py

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash

# Importa o Blueprint ('auth_bp') do arquivo __init__.py da mesma pasta
from . import auth_bp
from forms import LoginForm
from models import User

@auth_bp.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        u = User.query.filter_by(username=form.username.data).first()
        # Verificação correta da senha (com hash)
        if u and u.active and check_password_hash(u.password, form.password.data):
            login_user(u)
            return redirect(url_for("main.index"))
        flash("Credenciais inválidas ou usuário inativo.", "danger")
    return render_template("auth/login.html", form=form)

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))