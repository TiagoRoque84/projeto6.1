
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import login_required
from extensions import db
from models import Document, DocumentType, Company
from forms import DocumentForm, DocTypeForm
from utils import save_file
from audit import log_action
from pdf_reports import documents_pdf as _documents_pdf
import io
from datetime import date, datetime as _dt, timedelta

documents_bp = Blueprint("documents", __name__, template_folder='../../templates/documents')

@documents_bp.route("/")
@login_required
def list():
    company_id = request.args.get("company_id", type=int)
    tipo_id = request.args.get("tipo_id", type=int)
    status = request.args.get("status", "")
    q = request.args.get("q","").strip()
    venc_de = request.args.get("venc_de")
    venc_ate = request.args.get("venc_ate")

    query = Document.query
    if company_id: query = query.filter_by(company_id=company_id)
    if tipo_id: query = query.filter_by(tipo_id=tipo_id)
    if q:
        like = f"%{q}%"
        query = query.filter((Document.descricao.ilike(like)) | (Document.numero.ilike(like)) | (Document.orgao_emissor.ilike(like)) | (Document.responsavel.ilike(like)))
    docs = query.order_by(Document.data_vencimento.asc()).all()

    if status:
        tmp=[]
        for d in docs:
            st = d.status
            if status=="vencido" and st=="Vencido": tmp.append(d)
            elif status=="a_vencer" and st=="A vencer": tmp.append(d)
            elif status=="vigente" and st=="Vigente": tmp.append(d)
        docs = tmp

    def parse_date(s):
        try: return _dt.strptime(s,"%Y-%m-%d").date()
        except: return None
    d1, d2 = parse_date(venc_de), parse_date(venc_ate)
    if d1: docs = [d for d in docs if d.data_vencimento and d.data_vencimento >= d1]
    if d2: docs = [d for d in docs if d.data_vencimento and d.data_vencimento <= d2]

    companies = Company.query.order_by(Company.razao_social).all()
    tipos = DocumentType.query.order_by(DocumentType.nome).all()
    return render_template("documents/list.html", items=docs, companies=companies, tipos=tipos, company_id=company_id, tipo_id=tipo_id, status=status, q=q, venc_de=venc_de, venc_ate=venc_ate)

@documents_bp.route("/new", methods=["GET","POST"])
@login_required
def new():
    form = DocumentForm()
    form.company_id.choices = [(c.id, c.razao_social) for c in Company.query.order_by(Company.razao_social)]
    form.tipo_id.choices = [(t.id, t.nome) for t in DocumentType.query.order_by(DocumentType.nome)]
    if form.validate_on_submit():
        d = Document(**{k:getattr(form,k).data for k in ("company_id","tipo_id","descricao","numero","orgao_emissor","responsavel","data_expedicao","data_vencimento")})
        if form.arquivo.data:
            d.arquivo_path = save_file(form.arquivo.data, "docs")
        db.session.add(d); db.session.commit()
        log_action("create","Document", d.id, {"descricao": d.descricao})
        flash("Documento criado.", "success")
        return redirect(url_for("documents.list"))
    return render_template("documents/form.html", form=form, title="Novo Documento")

@documents_bp.route("/<int:doc_id>/edit", methods=["GET","POST"])
@login_required
def edit(doc_id):
    d = Document.query.get_or_404(doc_id)
    form = DocumentForm(obj=d)
    form.company_id.choices = [(c.id, c.razao_social) for c in Company.query.order_by(Company.razao_social)]
    form.tipo_id.choices = [(t.id, t.nome) for t in DocumentType.query.order_by(DocumentType.nome)]
    if form.validate_on_submit():
        for f in form:
            if hasattr(d, f.name): setattr(d, f.name, f.data)
        if form.arquivo.data:
            d.arquivo_path = save_file(form.arquivo.data, "docs")
        db.session.commit()
        log_action("update","Document", d.id, {"descricao": d.descricao})
        flash("Documento atualizado.", "success")
        return redirect(url_for("documents.list"))
    return render_template("documents/form.html", form=form, title="Editar Documento")

@documents_bp.route("/tipos")
@login_required
def tipos():
    items = DocumentType.query.order_by(DocumentType.nome).all()
    return render_template("documents/types_list.html", items=items)

@documents_bp.route("/tipos/new", methods=["GET","POST"])
@login_required
def tipos_new():
    form = DocTypeForm()
    if form.validate_on_submit():
        t = DocumentType(nome=form.nome.data)
        db.session.add(t); db.session.commit()
        flash("Tipo criado.", "success")
        return redirect(url_for("documents.tipos"))
    return render_template("documents/type_form.html", form=form, title="Novo Tipo de Documento")

@documents_bp.route("/tipos/<int:tid>/edit", methods=["GET","POST"])
@login_required
def tipos_edit(tid):
    t = DocumentType.query.get_or_404(tid)
    form = DocTypeForm(obj=t)
    if form.validate_on_submit():
        t.nome = form.nome.data
        db.session.commit()
        flash("Tipo atualizado.", "success")
        return redirect(url_for("documents.tipos"))
    return render_template("documents/type_form.html", form=form, title="Editar Tipo de Documento")

@documents_bp.route("/exportar.pdf")
@login_required
def export_pdf_filtered():
    company_id = request.args.get("company_id", type=int)
    tipo_id = request.args.get("tipo_id", type=int)
    status = request.args.get("status", "")
    q = request.args.get("q","").strip()
    de = request.args.get("venc_de"); ate = request.args.get("venc_ate")

    query = Document.query
    if company_id: query = query.filter(Document.company_id == int(company_id))
    if tipo_id: query = query.filter(Document.tipo_id == int(tipo_id))
    if q:
        like = f"%{q}%"
        query = query.filter((Document.descricao.ilike(like)) | (Document.numero.ilike(like)) | (Document.orgao_emissor.ilike(like)) | (Document.responsavel.ilike(like)))
    docs = query.order_by(Document.data_vencimento.asc()).all()

    from datetime import datetime as _dt
    if status:
        tmp = []
        for d in docs:
            st = d.status
            if status == "vencido" and st == "Vencido": tmp.append(d)
            elif status == "a_vencer" and st == "A vencer": tmp.append(d)
            elif status == "vigente" and st == "Vigente": tmp.append(d)
        docs = tmp
    def parse_date(s):
        try: return _dt.strptime(s, "%Y-%m-%d").date()
        except: return None
    d1, d2 = parse_date(de), parse_date(ate)
    if d1: docs = [d for d in docs if d.data_vencimento and d.data_vencimento >= d1]
    if d2: docs = [d for d in docs if d.data_vencimento and d.data_vencimento <= d2]

    bio = io.BytesIO()
    _documents_pdf(bio, current_app, docs, titulo="Documentos (filtro aplicado)")
    bio.seek(0)
    return send_file(bio, as_attachment=True, download_name="documentos_filtro.pdf", mimetype="application/pdf")

@documents_bp.route("/exportar_vencidos.pdf")
@login_required
def export_pdf_vencidos():
    hoje = date.today()
    docs = Document.query.filter(Document.data_vencimento < hoje).order_by(Document.data_vencimento.asc()).all()
    bio = io.BytesIO()
    _documents_pdf(bio, current_app, docs, titulo="Documentos Vencidos")
    bio.seek(0)
    return send_file(bio, as_attachment=True, download_name="documentos_vencidos.pdf", mimetype="application/pdf")

@documents_bp.route("/exportar_a_vencer.pdf")
@login_required
def export_pdf_a_vencer():
    hoje = date.today(); em_30 = hoje + timedelta(days=30)
    docs = Document.query.filter(Document.data_vencimento >= hoje, Document.data_vencimento <= em_30).order_by(Document.data_vencimento.asc()).all()
    bio = io.BytesIO()
    _documents_pdf(bio, current_app, docs, titulo="Documentos a Vencer (30 dias)")
    bio.seek(0)
    return send_file(bio, as_attachment=True, download_name="documentos_a_vencer.pdf", mimetype="application/pdf")
