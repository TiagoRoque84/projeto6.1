# models.py

from datetime import datetime, date
from extensions import db
from flask_login import UserMixin
import pytz
from sqlalchemy import func, or_

def now_sao_paulo():
    """Retorna o horário atual no fuso de São Paulo."""
    return datetime.now(pytz.timezone('America/Sao_Paulo'))

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(120))
    action = db.Column(db.String(50))
    entity = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    payload = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=now_sao_paulo)

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
    is_default = db.Column(db.Boolean, default=False)

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
    filho_menor14 = db.Column(db.Boolean)
    escolaridade = db.Column(db.String(40))
    company = db.relationship("Company")
    funcao = db.relationship("Funcao")
    def tempo_de_casa(self):
        if not self.data_admissao: return ""
        hoje = date.today()
        dias = (hoje - self.data_admissao).days
        anos, meses = dias // 365, (dias % 365) // 30
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
    created_at = db.Column(db.DateTime, default=now_sao_paulo)
    company = db.relationship("Company")
    tipo = db.relationship("DocumentType")
    @property
    def status(self):
        if not self.data_vencimento: return "Sem vencimento"
        hoje = date.today()
        if self.data_vencimento < hoje: return "Vencido"
        if (self.data_vencimento - hoje).days <= 30: return "A vencer"
        return "Vigente"

class EmployeeDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=False, index=True)
    tipo = db.Column(db.String(80))
    descricao = db.Column(db.String(200))
    arquivo_path = db.Column(db.String(300))
    uploaded_at = db.Column(db.DateTime, default=now_sao_paulo)
    employee = db.relationship("Employee", backref="documentos")

class CashMovement(db.Model):
    __tablename__ = "cash_movement"
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)
    valor = db.Column(db.Numeric(10,2), nullable=False)
    pagamento = db.Column(db.String(20), nullable=False)
    descricao = db.Column(db.String(255))
    ticket_ref = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=now_sao_paulo, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    placa = db.Column(db.String(10))
    material = db.Column(db.String(100))
    peso = db.Column(db.Numeric(10, 3))
    status = db.Column(db.String(20), default='Pendente')
    pagamento_id = db.Column(db.Integer, db.ForeignKey('cash_movement.id'), nullable=True)
    pagamentos_quitados = db.relationship('CashMovement', backref=db.backref('pagamento_de', remote_side=[id]))

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo_pessoa = db.Column(db.String(2), default='PF')
    nome_razao_social = db.Column(db.String(200), nullable=False)
    cpf_cnpj = db.Column(db.String(20), unique=False, nullable=True)
    telefone = db.Column(db.String(30))
    email = db.Column(db.String(150))
    cep = db.Column(db.String(9))
    logradouro = db.Column(db.String(200))
    numero = db.Column(db.String(20))
    complemento = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    uf = db.Column(db.String(2))
    ativo = db.Column(db.Boolean, default=True)
    movimentos = db.relationship('CashMovement', backref='customer', lazy=True, foreign_keys=[CashMovement.customer_id])

class Fornecedor(db.Model):
    __tablename__ = 'fornecedor'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    cnpj = db.Column(db.String(20), unique=True)
    epis = db.relationship('EPI', backref='fornecedor', lazy=True)

class EPI(db.Model):
    __tablename__ = 'epi'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    ca = db.Column(db.String(50))
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedor.id'), nullable=True)
    estoque = db.Column(db.Integer, default=0)

class EPISaida(db.Model):
    __tablename__ = 'epi_saida'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    retirado_por = db.Column(db.String(200), nullable=False)
    data_saida = db.Column(db.DateTime, default=now_sao_paulo)
    receipt_pdf_path = db.Column(db.String(300))
    
    employee = db.relationship('Employee')
    items = db.relationship('MovimentacaoEPI', backref='saida', lazy='dynamic', cascade="all, delete-orphan")

class MovimentacaoEPI(db.Model):
    __tablename__ = 'movimentacao_epi'
    id = db.Column(db.Integer, primary_key=True)
    epi_id = db.Column(db.Integer, db.ForeignKey('epi.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    data_movimentacao = db.Column(db.DateTime, default=now_sao_paulo)
    retirado_por = db.Column(db.String(200)) 
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    saida_id = db.Column(db.Integer, db.ForeignKey('epi_saida.id'), nullable=True)

    epi = db.relationship('EPI', backref='movimentacoes')
    employee = db.relationship('Employee')

class Servico(db.Model):
    __tablename__ = 'servico'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False, unique=True)

class Agendamento(db.Model):
    __tablename__ = 'agendamento'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    servico_id = db.Column(db.Integer, db.ForeignKey('servico.id'), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False)
    local = db.Column(db.String(300))
    observacao = db.Column(db.Text)
    status = db.Column(db.String(50), default='Agendado')
    visitante_nome = db.Column(db.String(200), nullable=True)
    customer = db.relationship('Customer', backref='agendamentos')
    servico = db.relationship('Servico', backref='agendamentos')

class Proposal(db.Model):
    __tablename__ = 'proposal'
    id = db.Column(db.Integer, primary_key=True)
    issuing_company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    attention = db.Column(db.String(200))
    representative_name = db.Column(db.String(200))
    status = db.Column(db.String(20), default='Pendente', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    issuing_company = db.relationship('Company', backref='proposals')
    customer = db.relationship('Customer', backref='proposals')
    items = db.relationship('ProposalItem', backref='proposal', cascade="all, delete-orphan")

    @property
    def total_value(self):
        return sum(item.total for item in self.items)

class ProposalItem(db.Model):
    __tablename__ = 'proposal_item'
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposal.id'), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    unit = db.Column(db.String(50))
    value = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    
    @property
    def total(self):
        return self.value

class Vehicle(db.Model):
    __tablename__ = 'vehicle'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.String(300))
    placa = db.Column(db.String(10), unique=True, nullable=False)
    renavam = db.Column(db.String(20), unique=True)
    venc_licenciamento = db.Column(db.Date)
    
    manutencoes = db.relationship('MaintenanceLog', backref='vehicle', lazy='dynamic', order_by="desc(MaintenanceLog.data)", cascade="all, delete-orphan")
    documentos = db.relationship('VehicleDocument', backref='vehicle', lazy='dynamic', cascade="all, delete-orphan")

class MaintenanceLog(db.Model):
    __tablename__ = 'maintenance_log'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    data = db.Column(db.Date, nullable=False)
    km_atual = db.Column(db.Integer)
    tipo_servico = db.Column(db.String(100), default="Troca de Óleo")
    local = db.Column(db.String(200))
    oleo_utilizado = db.Column(db.String(100))
    responsavel = db.Column(db.String(150))
    
    trocou_filtro = db.Column(db.Boolean, default=False)
    km_proxima_troca = db.Column(db.Integer)
    data_proxima_troca = db.Column(db.Date)

class VehicleDocument(db.Model):
    __tablename__ = 'vehicle_document'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    tipo = db.Column(db.String(80))
    descricao = db.Column(db.String(200))
    arquivo_path = db.Column(db.String(300))
    uploaded_at = db.Column(db.DateTime, default=now_sao_paulo)