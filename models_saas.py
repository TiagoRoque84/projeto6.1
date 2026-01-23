# models_saas.py
"""
Modelos específicos para o sistema SaaS Multi-Tenant
"""

from datetime import datetime, timedelta
from extensions import db
from flask_login import UserMixin
import pytz
import secrets
import string

def now_sao_paulo():
    """Retorna o horário atual no fuso de São Paulo."""
    return datetime.now(pytz.timezone('America/Sao_Paulo'))

# =============================================
# TENANT (Inquilino/Cliente SaaS)
# =============================================
class Tenant(db.Model):
    """
    Representa um cliente/inquilino do SaaS.
    Cada tenant tem seus próprios dados isolados.
    """
    __tablename__ = 'tenant'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificação
    subdomain = db.Column(db.String(50), unique=True, nullable=False, index=True)
    company_name = db.Column(db.String(200), nullable=False)
    
    # Contato principal
    contact_name = db.Column(db.String(200))
    contact_email = db.Column(db.String(150), unique=True, nullable=False)
    contact_phone = db.Column(db.String(30))
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_sao_paulo)
    activated_at = db.Column(db.DateTime)
    deactivated_at = db.Column(db.DateTime)
    
    # Trial
    trial_ends_at = db.Column(db.DateTime)
    is_trial = db.Column(db.Boolean, default=True)
    
    # Limites do plano
    max_companies = db.Column(db.Integer, default=1)
    max_users = db.Column(db.Integer, default=3)
    max_employees = db.Column(db.Integer, default=0)
    storage_limit_gb = db.Column(db.Integer, default=5)
    
    # Configurações de notificação
    alert_email = db.Column(db.String(500), default="")  # E-mails separados por ;
    
    # Relações
    subscription = db.relationship('Subscription', backref='tenant', uselist=False, cascade='all, delete-orphan')
    features = db.relationship('TenantFeature', backref='tenant', cascade='all, delete-orphan')
    users = db.relationship('User', backref='tenant_rel', foreign_keys='User.tenant_id')
    
    def __repr__(self):
        return f'<Tenant {self.subdomain}>'
    
    @property
    def is_trial_expired(self):
        """Verifica se o trial expirou"""
        if not self.is_trial or not self.trial_ends_at:
            return False
        # Tornar trial_ends_at aware se for naive
        trial_end = self.trial_ends_at
        if trial_end.tzinfo is None:
            trial_end = pytz.timezone('America/Sao_Paulo').localize(trial_end)
        return datetime.now(pytz.timezone('America/Sao_Paulo')) > trial_end
    
    @property
    def trial_days_remaining(self):
        """Retorna quantos dias restam no trial"""
        if not self.is_trial or not self.trial_ends_at:
            return 0
        # Tornar trial_ends_at aware se for naive
        trial_end = self.trial_ends_at
        if trial_end.tzinfo is None:
            trial_end = pytz.timezone('America/Sao_Paulo').localize(trial_end)
        now = datetime.now(pytz.timezone('America/Sao_Paulo'))
        delta = trial_end - now
        return max(0, delta.days)
    
    def has_feature(self, feature_code):
        """Verifica se o tenant tem acesso a uma feature específica"""
        feature = TenantFeature.query.filter_by(
            tenant_id=self.id,
            feature_code=feature_code,
            is_enabled=True
        ).first()
        return feature is not None
    
    def get_current_usage(self):
        """Retorna estatísticas de uso atual"""
        from models import Company, User, Employee
        
        return {
            'companies': Company.query.filter_by(tenant_id=self.id).count(),
            'users': User.query.filter_by(tenant_id=self.id).count(),
            'employees': Employee.query.filter_by(tenant_id=self.id).count() if self.has_feature('hr') else 0,
        }
    
    def is_within_limits(self):
        """Verifica se o tenant está dentro dos limites do plano"""
        usage = self.get_current_usage()
        
        if usage['companies'] > self.max_companies:
            return False, f"Limite de empresas excedido ({usage['companies']}/{self.max_companies})"
        
        if usage['users'] > self.max_users:
            return False, f"Limite de usuários excedido ({usage['users']}/{self.max_users})"
        
        if self.max_employees > 0 and usage['employees'] > self.max_employees:
            return False, f"Limite de funcionários excedido ({usage['employees']}/{self.max_employees})"
        
        return True, "OK"


# =============================================
# SUBSCRIPTION (Assinatura)
# =============================================
class Subscription(db.Model):
    """
    Representa a assinatura de um tenant
    """
    __tablename__ = 'subscription'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), unique=True, nullable=False)
    
    # Plano
    plan_type = db.Column(db.String(20), nullable=False)  # basic, professional, enterprise
    price = db.Column(db.Numeric(10, 2))
    billing_cycle = db.Column(db.String(20), default='monthly')  # monthly, yearly
    
    # Status
    status = db.Column(db.String(20), default='trial')  # trial, active, suspended, cancelled, past_due
    
    # Datas
    current_period_start = db.Column(db.Date)
    current_period_end = db.Column(db.Date)
    next_billing_date = db.Column(db.Date)
    cancelled_at = db.Column(db.DateTime)
    
    # Pagamento
    payment_method = db.Column(db.String(50))  # credit_card, boleto, pix
    gateway_customer_id = db.Column(db.String(100))  # ID no gateway de pagamento
    gateway_subscription_id = db.Column(db.String(100))  # ID da subscription no gateway
    
    # Histórico
    created_at = db.Column(db.DateTime, default=now_sao_paulo)
    updated_at = db.Column(db.DateTime, default=now_sao_paulo, onupdate=now_sao_paulo)
    
    def __repr__(self):
        return f'<Subscription {self.plan_type} - {self.status}>'
    
    @property
    def is_active(self):
        """Verifica se a assinatura está ativa"""
        return self.status in ['trial', 'active']
    
    @property
    def days_until_renewal(self):
        """Dias até a próxima renovação"""
        if not self.next_billing_date:
            return None
        delta = self.next_billing_date - datetime.now().date()
        return delta.days


# =============================================
# TENANT FEATURE (Feature/Módulo habilitado)
# =============================================
class TenantFeature(db.Model):
    """
    Relaciona quais features/módulos estão habilitados para cada tenant
    """
    __tablename__ = 'tenant_feature'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    feature_code = db.Column(db.String(50), nullable=False)  # documents, hr, fleet, etc.
    is_enabled = db.Column(db.Boolean, default=True)
    
    # Metadata
    enabled_at = db.Column(db.DateTime, default=now_sao_paulo)
    
    # Constraint única: um tenant não pode ter a mesma feature duplicada
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'feature_code', name='unique_tenant_feature'),
    )
    
    def __repr__(self):
        return f'<TenantFeature {self.feature_code} for tenant {self.tenant_id}>'


# =============================================
# SUPER ADMIN (Administrador da plataforma)
# =============================================
class SuperAdmin(db.Model, UserMixin):
    """
    Usuário super administrador que gerencia toda a plataforma SaaS
    """
    __tablename__ = 'super_admin'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    nome_completo = db.Column(db.String(200))
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_sao_paulo)
    last_login = db.Column(db.DateTime)
    
    def get_id(self):
        return f"super_{self.id}"
    
    def __repr__(self):
        return f'<SuperAdmin {self.username}>'


# =============================================
# TENANT INVITATION (Convite para novos usuários)
# =============================================
class TenantInvitation(db.Model):
    """
    Convites para novos usuários se juntarem a um tenant
    """
    __tablename__ = 'tenant_invitation'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    
    email = db.Column(db.String(150), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    
    # Status
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=now_sao_paulo)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)
    
    # Quem convidou
    invited_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    @staticmethod
    def generate_token():
        """Gera um token único para o convite"""
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    
    @property
    def is_expired(self):
        """Verifica se o convite expirou"""
        return datetime.now(pytz.timezone('America/Sao_Paulo')) > self.expires_at
    
    @property
    def is_valid(self):
        """Verifica se o convite é válido"""
        return not self.is_used and not self.is_expired
    
    def __repr__(self):
        return f'<TenantInvitation {self.email}>'


# =============================================
# PAYMENT (Pagamentos/Faturas)
# =============================================
class Payment(db.Model):
    """
    Pagamentos/Faturas dos tenants
    Histórico de cobranças e pagamentos
    """
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    
    # Dados da fatura
    invoice_number = db.Column(db.String(50), unique=True)  # Número da fatura
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # Valor
    description = db.Column(db.String(255))  # Descrição (ex: "Mensalidade Janeiro/2026")
    
    # Datas
    due_date = db.Column(db.Date, nullable=False)  # Data de vencimento
    paid_at = db.Column(db.DateTime(timezone=True))  # Data do pagamento
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(pytz.timezone('America/Sao_Paulo')))
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, paid, overdue, cancelled
    
    # Gateway de pagamento (futuro)
    payment_method = db.Column(db.String(50))  # credit_card, boleto, pix, etc
    transaction_id = db.Column(db.String(100))  # ID da transação no gateway
    
    # Observações
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Payment {self.invoice_number} - {self.status}>'
    
    @property
    def is_overdue(self):
        """Verifica se a fatura está vencida"""
        if self.status == 'paid':
            return False
        from datetime import date
        return date.today() > self.due_date
    
    @property
    def formatted_amount(self):
        """Retorna valor formatado"""
        return f"R$ {float(self.amount):.2f}"
