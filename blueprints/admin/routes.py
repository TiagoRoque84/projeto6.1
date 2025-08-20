
from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required
from utils import admin_required, save_file
from alerts import send_alerts
from models import AuditLog
import os, shutil

admin_bp = Blueprint("admin", __name__, template_folder='../../templates/admin')

@admin_bp.route("/alertas/disparar")
@login_required
@admin_required
def trigger_alerts():
    send_alerts()
    flash("Alertas disparados.", "success")
    return redirect(url_for("main.index"))

@admin_bp.route("/auditoria")
@login_required
@admin_required
def audit():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(500).all()
    return render_template("admin/audit.html", logs=logs)

@admin_bp.route("/config", methods=["GET","POST"])
@login_required
@admin_required
def settings():
    from flask_wtf import FlaskForm
    from wtforms import FileField, SubmitField
    from wtforms.validators import Optional
    class SettingsForm(FlaskForm):
        logo_sidebar = FileField("Logo (sidebar)", validators=[Optional()])
        logo_login = FileField("Logo (tela de login)", validators=[Optional()])
        submit = SubmitField("Salvar")
    form = SettingsForm()
    if form.validate_on_submit():
        msgs=[]
        if form.logo_sidebar.data:
            p = save_file(form.logo_sidebar.data, "branding")
            if p:
                src = os.path.join(current_app.root_path, p)
                dst = os.path.join(current_app.root_path, "static", "img", "logo.png")
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst); msgs.append("Logo da sidebar atualizada.")
        if form.logo_login.data:
            p = save_file(form.logo_login.data, "branding")
            if p:
                src = os.path.join(current_app.root_path, p)
                dst = os.path.join(current_app.root_path, "static", "img", "logo-login.png")
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst); msgs.append("Logo da tela de login atualizada.")
        flash(" ".join(msgs) if msgs else "Nenhum arquivo enviado.", "success" if msgs else "info")
    return render_template("admin/settings.html", form=form)
