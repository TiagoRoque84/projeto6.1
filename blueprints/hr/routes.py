# blueprints/hr/routes.py
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, send_file, current_app
)
from flask_login import login_required
from extensions import db
from models import Employee, Company, Funcao, EmployeeDocument
from forms import EmployeeForm, FuncaoForm, EmployeeDocForm
from utils import save_file
from pdf_reports import employee_pdf
import io, requests

# --- CRIA O BLUEPRINT PRIMEIRO ---
hr_bp = Blueprint("rh", __name__)

# ---------------------- LISTAGEM DE COLABORADORES ----------------------
@hr_bp.route("/colaboradores")
@login_required
def employees():
    q = request.args.get("q", "").strip()
    ativo = request.args.get("ativo", "")
    mes_aniversario = request.args.get("mes", "")

    query = Employee.query
    if q:
        like = f"%{q}%"
        query = query.filter(Employee.nome.ilike(like))
    if ativo in ("1", "0"):
        query = query.filter_by(ativo=(ativo == "1"))

    items = query.order_by(Employee.nome).all()

    # filtro de aniversariantes (opcional)
    if mes_aniversario:
        try:
            m = int(mes_aniversario)
            items = [e for e in items if e.data_nascimento and e.data_nascimento.month == m]
        except Exception:
            pass

    return render_template("hr/employees_list.html",
                           items=items, q=q, ativo=ativo, mes=mes_aniversario)

def _apply_employee_form(e: Employee, form: EmployeeForm):
    """Copia dados do form para o modelo, ajustando campos especiais."""
    for f in form:
        if hasattr(e, f.name):
            v = f.data
            if f.name == "company_id" and v == 0:
                v = None
            if f.name == "funcao_id" and v == 0:
                v = None
            if f.name == "filho_menor14":
                if v == "1":
                    v = True
                elif v == "0":
                    v = False
                else:
                    v = None
            setattr(e, f.name, v)

# ---------------------- NOVO COLABORADOR ----------------------
@hr_bp.route("/colaboradores/novo", methods=["GET", "POST"])
@hr_bp.route("/colaboradores/new", methods=["GET", "POST"])  # compat
@login_required
def employees_new():
    form = EmployeeForm()
    form.company_id.choices = [(0, "-")] + [
        (c.id, c.razao_social) for c in Company.query.order_by(Company.razao_social)
    ]
    form.funcao_id.choices = [(0, "-")] + [
        (f.id, f.nome) for f in Funcao.query.order_by(Funcao.nome)
    ]

    if form.validate_on_submit():
        e = Employee()
        _apply_employee_form(e, form)
        if form.foto.data:
            e.foto_path = save_file(form.foto.data, "fotos")
        db.session.add(e)
        db.session.commit()
        flash("Colaborador criado.", "success")
        return redirect(url_for("rh.employees"))

    return render_template("hr/employee_form.html", form=form, title="Novo Colaborador")

# ---------------------- EDITAR COLABORADOR ----------------------
@hr_bp.route("/colaboradores/<int:emp_id>/edit", methods=["GET", "POST"])
@login_required
def employees_edit(emp_id):
    e = Employee.query.get_or_404(emp_id)
    form = EmployeeForm(obj=e)
    # normaliza combobox booleano
    form.filho_menor14.data = "" if e.filho_menor14 is None else ("1" if e.filho_menor14 else "0")

    form.company_id.choices = [(0, "-")] + [
        (c.id, c.razao_social) for c in Company.query.order_by(Company.razao_social)
    ]
    form.funcao_id.choices = [(0, "-")] + [
        (f.id, f.nome) for f in Funcao.query.order_by(Funcao.nome)
    ]

    if form.validate_on_submit():
        _apply_employee_form(e, form)
        if form.foto.data:
            e.foto_path = save_file(form.foto.data, "fotos")
        db.session.commit()
        flash("Colaborador atualizado.", "success")
        return redirect(url_for("rh.employees"))

    return render_template("hr/employee_form.html", form=form, title="Editar Colaborador")

# ---------------------- EXCLUIR COLABORADOR ----------------------
@hr_bp.route("/colaboradores/<int:emp_id>/delete", methods=["POST"])
@login_required
def employees_delete(emp_id):
    e = Employee.query.get_or_404(emp_id)
    db.session.delete(e)
    db.session.commit()
    flash("Colaborador excluído.", "success")
    return redirect(url_for("rh.employees"))

# ---------------------- PDF DO COLABORADOR ----------------------
@hr_bp.route("/colaboradores/<int:emp_id>/pdf")
@login_required
def employees_pdf(emp_id):
    e = Employee.query.get_or_404(emp_id)
    bio = io.BytesIO()
    employee_pdf(bio, current_app, e)
    bio.seek(0)
    return send_file(bio, as_attachment=True,
                     download_name=f"colaborador_{e.id}.pdf",
                     mimetype="application/pdf")

# ---------------------- DOCS DO COLABORADOR ----------------------
@hr_bp.route("/colaboradores/<int:emp_id>/docs", methods=["GET", "POST"])
@login_required
def employee_docs(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    form = EmployeeDocForm()

    if form.validate_on_submit():
        path = save_file(form.arquivo.data, "func_docs") if form.arquivo.data else None
        d = EmployeeDocument(
            employee_id=emp.id,
            tipo=form.tipo.data,
            descricao=form.descricao.data,
            arquivo_path=path
        )
        db.session.add(d)
        db.session.commit()
        flash("Documento anexado.", "success")
        return redirect(url_for("rh.employee_docs", emp_id=emp.id))

    q = request.args.get("q", "").strip().lower()
    docs = list(emp.documentos)
    if q:
        docs = [
            d for d in docs
            if (d.tipo and q in d.tipo.lower()) or (d.descricao and q in d.descricao.lower())
        ]

    return render_template("hr/employee_docs.html", emp=emp, form=form, docs=docs)

# ---------------------- API CEP ----------------------
@hr_bp.route("/api/cep/<cep>")
@login_required
def api_cep(cep):
    try:
        r = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=10)
        return r.json(), r.status_code
    except Exception:
        return {"erro": True}, 400

# ===================== FUNÇÕES (CARGOS) =====================
@hr_bp.route("/funcoes", methods=["GET", "POST"])
@login_required
def funcoes():
    form = FuncaoForm()
    itens = Funcao.query.order_by(Funcao.nome).all()

    if form.validate_on_submit():
        f = Funcao(nome=form.nome.data.strip())
        db.session.add(f)
        db.session.commit()
        flash("Função criada.", "success")
        return redirect(url_for("rh.funcoes"))

    return render_template("hr/funcoes.html", form=form, itens=itens)

@hr_bp.route("/funcoes/<int:funcao_id>/edit", methods=["GET", "POST"])
@login_required
def funcoes_edit(funcao_id):
    f = Funcao.query.get_or_404(funcao_id)
    form = FuncaoForm(obj=f)

    if form.validate_on_submit():
        f.nome = form.nome.data.strip()
        db.session.commit()
        flash("Função atualizada.", "success")
        return redirect(url_for("rh.funcoes"))

    itens = Funcao.query.order_by(Funcao.nome).all()
    return render_template("hr/funcoes.html", form=form, itens=itens, editar=f)

@hr_bp.route("/funcoes/<int:funcao_id>/delete", methods=["POST"])
@login_required
def funcoes_delete(funcao_id):
    f = Funcao.query.get_or_404(funcao_id)
    db.session.delete(f)
    db.session.commit()
    flash("Função removida.", "success")
    return redirect(url_for("rh.funcoes"))
# =================== FIM FUNÇÕES (CARGOS) ===================
