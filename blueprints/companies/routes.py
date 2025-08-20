
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app, jsonify
from flask_login import login_required
from extensions import db
from models import Company
from forms import CompanyForm
from audit import log_action
from pdf_reports import company_pdf as _company_pdf
import io, requests

companies_bp = Blueprint("companies", __name__, template_folder='../../templates/companies')

@companies_bp.route("/")
@login_required
def list():
    q = request.args.get("q","").strip()
    query = Company.query
    if q:
        like = f"%{q}%"
        query = query.filter((Company.razao_social.ilike(like)) | (Company.nome_fantasia.ilike(like)) | (Company.cnpj.ilike(like)))
    items = query.order_by(Company.razao_social).all()
    return render_template("companies/list.html", items=items, q=q)

@companies_bp.route("/new", methods=["GET","POST"])
@login_required
def new():
    form = CompanyForm()
    if form.validate_on_submit():
        c = Company(**{f.name:getattr(form,f.name).data for f in form if hasattr(Company, f.name)})
        db.session.add(c); db.session.commit()
        log_action("create","Company", c.id, {"cnpj": c.cnpj})
        flash("Empresa criada.", "success")
        return redirect(url_for("companies.list"))
    return render_template("companies/form.html", form=form, title="Nova Empresa")

@companies_bp.route("/<int:company_id>/edit", methods=["GET","POST"])
@login_required
def edit(company_id):
    c = Company.query.get_or_404(company_id)
    form = CompanyForm(obj=c)
    if form.validate_on_submit():
        for f in form:
            if hasattr(c, f.name): setattr(c, f.name, f.data)
        db.session.commit(); log_action("update","Company", c.id, {"cnpj": c.cnpj})
        flash("Empresa atualizada.", "success")
        return redirect(url_for("companies.list"))
    return render_template("companies/form.html", form=form, title="Editar Empresa")

@companies_bp.route("/<int:company_id>/pdf")
@login_required
def company_pdf(company_id):
    c = Company.query.get_or_404(company_id)
    bio = io.BytesIO()
    _company_pdf(bio, current_app, c)
    bio.seek(0)
    return send_file(bio, as_attachment=True, download_name=f"empresa_{c.id}.pdf", mimetype="application/pdf")

@companies_bp.route("/api/cnpj/<cnpj>")
@login_required
def api_cnpj(cnpj):
    try:
        r = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}", timeout=10)
        if r.status_code==200:
            d = r.json()
            out = {
                "razao_social": d.get("razao_social") or d.get("razao_social_nome_empresarial") or "",
                "nome_fantasia": d.get("nome_fantasia") or d.get("nome_fantasia_empresarial") or "",
                "cep": (d.get("cep") or "").replace("-", ""),
                "logradouro": (d.get("descricao_tipo_logradouro") or "") + " " + (d.get("logradouro") or ""),
                "bairro": d.get("bairro") or d.get("bairro_distrito") or "",
                "cidade": d.get("municipio") or d.get("cidade") or "",
                "uf": d.get("uf") or "",
                "numero": d.get("numero") or "",
                "complemento": d.get("complemento") or "",
            }
            return jsonify(out), 200
    except Exception:
        pass
    return jsonify({"erro": True}), 400
