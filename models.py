
from datetime import datetime, date
from extensions import db
from flask_login import UserMixin

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(120))
    action = db.Column(db.String(50))
    entity = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    payload = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="admin")
    active = db.Column(db.Boolean, default=True)
    nome_completo = db.Column(db.String(200), default="")

    def get_id(self): return str(self.id)

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    razao_social = db.Column(db.String(200), nullable=False)
    nome_fantasia = db.Column(db.String(200), default="")
    cnpj = db.Column(db.String(20), unique=True)
    inscricao_estadual = db.Column(db.String(50))
    cep = db.Column(db.String(9))
    logradouro = db.Column(db.String(200))
    numero = db.Column(db.String(20))
    complemento = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    uf = db.Column(db.String(2))
    ativa = db.Column(db.Boolean, default=True)
    alert_email = db.Column(db.String(500), default="")
    alert_whatsapp = db.Column(db.String(500), default="")

class Funcao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"))
    funcao_id = db.Column(db.Integer, db.ForeignKey("funcao.id"))
    ativo = db.Column(db.Boolean, default=True)
    nome = db.Column(db.String(200), nullable=False)
    cpf = db.Column(db.String(14))
    rg = db.Column(db.String(20))
    data_nascimento = db.Column(db.Date)
    genero = db.Column(db.String(20))
    estado_civil = db.Column(db.String(30))
    data_admissao = db.Column(db.Date)
    salario = db.Column(db.String(30))
    jornada = db.Column(db.String(30))
    fone = db.Column(db.String(30))
    celular = db.Column(db.String(30))
    email = db.Column(db.String(150))
    cep = db.Column(db.String(9))
    logradouro = db.Column(db.String(200))
    numero = db.Column(db.String(20))
    complemento = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    uf = db.Column(db.String(2))
    banco = db.Column(db.String(50))
    agencia = db.Column(db.String(20))
    conta = db.Column(db.String(20))
    tipo_conta = db.Column(db.String(20))
    pix_tipo = db.Column(db.String(20))
    pix_chave = db.Column(db.String(120))
    aso_tipo = db.Column(db.String(50))
    aso_validade = db.Column(db.Date)
    cnh = db.Column(db.String(30))
    cnh_validade = db.Column(db.Date)
    exame_toxico_validade = db.Column(db.Date)
    foto_path = db.Column(db.String(300))

    # Novos campos
    filho_menor14 = db.Column(db.Boolean)                # True/False
    escolaridade = db.Column(db.String(40))              # ex.: Médio completo

    company = db.relationship("Company")
    funcao = db.relationship("Funcao")

    def tempo_de_casa(self):
        if not self.data_admissao:
            return ""
        hoje = date.today()
        dias = (hoje - self.data_admissao).days
        anos = dias // 365
        meses = (dias % 365) // 30
        return f"{anos}a {meses}m" if anos or meses else f"{dias}d"

class DocumentType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"))
    tipo_id = db.Column(db.Integer, db.ForeignKey("document_type.id"))
    descricao = db.Column(db.String(200))
    numero = db.Column(db.String(50))
    orgao_emissor = db.Column(db.String(120))
    responsavel = db.Column(db.String(120))
    data_expedicao = db.Column(db.Date)
    data_vencimento = db.Column(db.Date)
    arquivo_path = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    company = db.relationship("Company")
    tipo = db.relationship("DocumentType")

    @property
    def status(self):
        if not self.data_vencimento:
            return "Sem vencimento"
        hoje = date.today()
        if self.data_vencimento < hoje:
            return "Vencido"
        if (self.data_vencimento - hoje).days <= 30:
            return "A vencer"
        return "Vigente"

class EmployeeDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=False, index=True)
    tipo = db.Column(db.String(80))
    descricao = db.Column(db.String(200))
    arquivo_path = db.Column(db.String(300))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship("Employee", backref="documentos")
