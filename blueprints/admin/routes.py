
from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request, g
from flask_login import login_required
from utils import admin_required, save_file
from alerts import send_alerts
from models import AuditLog
from extensions import db
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
    from wtforms import FileField, SubmitField, StringField
    from wtforms.validators import Optional
    
    class SettingsForm(FlaskForm):
        logo_sidebar = FileField("Logo (sidebar)", validators=[Optional()])
        logo_login = FileField("Logo (tela de login)", validators=[Optional()])
        alert_emails = StringField("E-mails para alertas (separar por ;)", validators=[Optional()])
        submit = SubmitField("Salvar")
    
    # Carregar e-mails de alertas do tenant atual
    current_alert_emails = ""
    if hasattr(g, 'tenant') and g.tenant:
        current_alert_emails = g.tenant.alert_email or ""
    
    form = SettingsForm()
    
    if request.method == 'GET':
        form.alert_emails.data = current_alert_emails
    
    if form.validate_on_submit():
        msgs=[]
        
        # Atualizar e-mails de alertas
        if hasattr(g, 'tenant') and g.tenant:
            g.tenant.alert_email = form.alert_emails.data.strip()
            db.session.commit()
            msgs.append("E-mails de alertas atualizados.")
        
        if form.logo_sidebar.data:
            p = save_file(form.logo_sidebar.data, "branding")
            if p:
                src = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'], p)
                dst = os.path.join(current_app.root_path, "static", "img", "logo.png")
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if os.path.exists(src):
                    shutil.copyfile(src, dst)
                    msgs.append("Logo da sidebar atualizada.")
                else:
                    msgs.append(f"Erro: arquivo não encontrado em {src}")
        if form.logo_login.data:
            p = save_file(form.logo_login.data, "branding")
            if p:
                src = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'], p)
                dst = os.path.join(current_app.root_path, "static", "img", "logo-login.png")
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if os.path.exists(src):
                    shutil.copyfile(src, dst)
                    msgs.append("Logo da tela de login atualizada.")
                else:
                    msgs.append(f"Erro: arquivo não encontrado em {src}")
        flash(" ".join(msgs) if msgs else "Nenhum arquivo enviado.", "success" if msgs else "info")
    return render_template("admin/settings.html", form=form)

