# models_financial.py
"""
Modelos para o Sistema Financeiro do Super Admin
"""

from datetime import datetime, date
from extensions import db
import pytz

def now_sao_paulo():
    return datetime.now(pytz.timezone('America/Sao_Paulo'))


class BankAccount(db.Model):
    """Contas Bancárias"""
    __tablename__ = 'bank_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Ex: "Banco do Brasil - Conta Corrente"
    bank_name = db.Column(db.String(100))  # Nome do banco
    agency = db.Column(db.String(20))
    account_number = db.Column(db.String(30))
    account_type = db.Column(db.String(20), default='corrente')  # corrente/poupança
    initial_balance = db.Column(db.Numeric(12, 2), default=0)
    current_balance = db.Column(db.Numeric(12, 2), default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_sao_paulo)
    
    # Relações
    transactions = db.relationship('FinancialTransaction', back_populates='bank_account', lazy='dynamic')
    
    def __repr__(self):
        return f'<BankAccount {self.name}>'
    
    @property
    def formatted_balance(self):
        return f"R$ {float(self.current_balance):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


class PaymentMethod(db.Model):
    """Formas de Pagamento"""
    __tablename__ = 'payment_methods'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # PIX, Dinheiro, etc
    description = db.Column(db.String(200))
    icon = db.Column(db.String(20))  # Emoji ou classe de ícone
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_sao_paulo)
    
    def __repr__(self):
        return f'<PaymentMethod {self.name}>'


class FinancialCategory(db.Model):
    """Categorias Financeiras (Receitas e Despesas)"""
    __tablename__ = 'financial_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'receita' ou 'despesa'
    description = db.Column(db.String(200))
    color = db.Column(db.String(7), default='#667eea')  # Cor hexadecimal para gráficos
    icon = db.Column(db.String(20))  # Emoji
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_sao_paulo)
    
    # Relações
    transactions = db.relationship('FinancialTransaction', back_populates='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<FinancialCategory {self.name} ({self.type})>'


class FinancialTransaction(db.Model):
    """Lançamentos Financeiros (Receitas e Despesas)"""
    __tablename__ = 'financial_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Tipo e Categoria
    type = db.Column(db.String(20), nullable=False)  # 'receita' ou 'despesa'
    category_id = db.Column(db.Integer, db.ForeignKey('financial_categories.id'))
    
    # Informações Básicas
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Datas
    due_date = db.Column(db.Date, nullable=False)
    payment_date = db.Column(db.Date)
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, paid, overdue, cancelled
    
    # Pagamento
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_methods.id'))
    bank_account_id = db.Column(db.Integer, db.ForeignKey('bank_accounts.id'))
    
    # Relacionamento com Tenant (opcional)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'))
    
    # Recorrência
    is_recurring = db.Column(db.Boolean, default=False)
    recurring_frequency = db.Column(db.String(20))  # mensal, anual
    
    # Extras
    attachment_path = db.Column(db.String(255))
    notes = db.Column(db.Text)
    
    # Auditoria
    created_by = db.Column(db.Integer, db.ForeignKey('super_admin.id'))
    created_at = db.Column(db.DateTime, default=now_sao_paulo)
    updated_at = db.Column(db.DateTime, default=now_sao_paulo, onupdate=now_sao_paulo)
    
    # Relações
    category = db.relationship('FinancialCategory', back_populates='transactions')
    payment_method = db.relationship('PaymentMethod')
    bank_account = db.relationship('BankAccount', back_populates='transactions')
    tenant = db.relationship('Tenant')
    
    def __repr__(self):
        return f'<FinancialTransaction {self.description} - R$ {self.amount}>'
    
    @property
    def is_overdue(self):
        """Verifica se está vencido"""
        if self.status == 'paid':
            return False
        return date.today() > self.due_date
    
    @property
    def formatted_amount(self):
        return f"R$ {float(self.amount):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def status_badge(self):
        """Retorna classe CSS do badge"""
        if self.status == 'paid':
            return 'success'
        elif self.is_overdue:
            return 'danger'
        elif self.status == 'cancelled':
            return 'secondary'
        return 'warning'
