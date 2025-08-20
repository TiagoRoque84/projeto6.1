
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from forms import LoginForm
from models import User

auth_bp = Blueprint("auth", __name__, template_folder='../../templates/auth')

@auth_bp.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        u = User.query.filter_by(username=form.username.data).first()
        if u and u.password == form.password.data and u.active:
            login_user(u)
            return redirect(url_for("main.index"))
        flash("Credenciais inválidas ou usuário inativo.", "danger")
    return render_template("auth/login.html", form=form)

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
