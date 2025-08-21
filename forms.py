# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, DateField, FileField, IntegerField, TextAreaField
# Importa o campo de data e hora
from wtforms.fields import DateTimeField
from wtforms.validators import DataRequired, Optional, Email, NumberRange

class LoginForm(FlaskForm):
    username = StringField("Usuário", validators=[DataRequired()])
    password = PasswordField("Senha", validators=[DataRequired()])
    submit = SubmitField("Entrar")

class CompanyForm(FlaskForm):
    razao_social = StringField("Razão Social", validators=[DataRequired()])
    nome_fantasia = StringField("Nome Fantasia")
    cnpj = StringField("CNPJ")
    inscricao_estadual = StringField("Inscrição Estadual")
    cep = StringField("CEP")
    logradouro = StringField("Logradouro")
    numero = StringField("Número")
    complemento = StringField("Complemento")
    bairro = StringField("Bairro")
    cidade = StringField("Cidade")
    uf = StringField("UF")
    ativa = BooleanField("Ativa")
    alert_email = StringField("E-mails para alertas (separar por ;)")
    alert_whatsapp = StringField("WhatsApp(s) para alertas (+55DDDNUM; separados por ;)")
    submit = SubmitField("Salvar")

class FuncaoForm(FlaskForm):
    nome = StringField("Nome", validators=[DataRequired()])
    submit = SubmitField("Salvar")

class EmployeeForm(FlaskForm):
    company_id = SelectField("Empresa", coerce=int, validators=[Optional()])
    funcao_id = SelectField("Função", coerce=int, validators=[Optional()])
    ativo = BooleanField("Ativo", default=True)
    nome = StringField("Nome completo", validators=[DataRequired()])
    cpf = StringField("CPF")
    rg = StringField("RG")
    data_nascimento = DateField("Nascimento", validators=[Optional()])
    genero = SelectField("Gênero", choices=[("",""),("M","Masculino"),("F","Feminino"),("O","Outro")])
    estado_civil = SelectField("Estado civil", choices=[("",""),("Solteiro","Solteiro"),("Casado","Casado"),("Divorciado","Divorciado"),("Viúvo","Viúvo")])
    data_admissao = DateField("Admissão", validators=[Optional()])
    salario = StringField("Salário (R$)")
    jornada = StringField("Jornada")
    fone = StringField("Telefone")
    celular = StringField("Celular")
    email = StringField("E-mail", validators=[Optional(), Email()])
    cep = StringField("CEP")
    logradouro = StringField("Logradouro")
    numero = StringField("Número")
    complemento = StringField("Complemento")
    bairro = StringField("Bairro")
    cidade = StringField("Cidade")
    uf = StringField("UF")
    banco = StringField("Banco")
    agencia = StringField("Agência")
    conta = StringField("Conta")
    tipo_conta = SelectField("Tipo de conta", choices=[("",""),("C/C","C/C"),("Salário","Salário"),("Poupança","Poupança")])
    pix_tipo = SelectField("Tipo de PIX", choices=[("",""),("CPF","CPF"),("CNPJ","CNPJ"),("Celular","Celular"),("E-mail","E-mail"),("Chave Aleatória","Chave Aleatória")])
    pix_chave = StringField("Chave PIX")
    aso_tipo = SelectField("ASO", choices=[("",""),("Admissional","Admissional"),("Periódico","Periódico"),("Mudança de Função","Mudança de Função"),("Retorno ao Trabalho","Retorno ao Trabalho"),("Demissional","Demissional")])
    aso_validade = DateField("Validade ASO", validators=[Optional()])
    cnh = StringField("CNH")
    cnh_validade = DateField("Validade CNH", validators=[Optional()])
    exame_toxico_validade = DateField("Validade Toxicológico", validators=[Optional()])
    foto = FileField("Foto (jpg/png)", validators=[Optional()])
    filho_menor14 = SelectField("Possui filho menor de 14 anos?", choices=[("", ""), ("1","Sim"), ("0","Não")], coerce=str, validators=[Optional()])
    escolaridade = SelectField(
        "Escolaridade",
        choices=[
            ("",""),
            ("Fundamental incompleto","Fundamental incompleto"),
            ("Fundamental completo","Fundamental completo"),
            ("Médio incompleto","Médio incompleto"),
            ("Médio completo","Médio completo"),
            ("Técnico","Técnico"),
            ("Superior incompleto","Superior incompleto"),
            ("Superior completo","Superior completo"),
            ("Pós-graduação","Pós-graduação"),
        ],
        validators=[Optional()],
    )
    submit = SubmitField("Salvar")

class DocumentForm(FlaskForm):
    company_id = SelectField("Empresa", coerce=int, validators=[Optional()])
    tipo_id = SelectField("Tipo de Documento", coerce=int, validators=[Optional()])
    descricao = StringField("Descrição")
    numero = StringField("Número")
    orgao_emissor = StringField("Órgão Emissor")
    responsavel = StringField("Responsável")
    data_expedicao = DateField("Data de Expedição", validators=[Optional()])
    data_vencimento = DateField("Data de Vencimento", validators=[Optional()])
    arquivo = FileField("Anexo (PDF/JPG/PNG)", validators=[Optional()])
    submit = SubmitField("Salvar")

class DocTypeForm(FlaskForm):
    nome = StringField("Nome do tipo de documento", validators=[DataRequired()])
    submit = SubmitField("Salvar")

class EmployeeDocForm(FlaskForm):
    tipo = SelectField("Tipo", choices=[("RG","RG"),("CPF","CPF"),("CNH","CNH"),("ASO","ASO"),("Contrato","Contrato"),("Comprovante de Endereço","Comprovante de Endereço"),("Outros","Outros")])
    descricao = StringField("Descrição")
    arquivo = FileField("Arquivo (PDF/JPG/PNG)", validators=[Optional()])
    submit = SubmitField("Enviar")

class CustomerForm(FlaskForm):
    tipo_pessoa = SelectField("Tipo", choices=[('PF', 'Pessoa Física'), ('PJ', 'Pessoa Jurídica')], default='PF', validators=[DataRequired()])
    nome_razao_social = StringField("Nome / Razão Social", validators=[DataRequired()])
    cpf_cnpj = StringField("CPF / CNPJ")
    telefone = StringField("Telefone")
    email = StringField("E-mail", validators=[Optional(), Email()])
    cep = StringField("CEP")
    logradouro = StringField("Logradouro")
    numero = StringField("Número")
    complemento = StringField("Complemento")
    bairro = StringField("Bairro")
    cidade = StringField("Cidade")
    uf = StringField("UF")
    ativo = BooleanField("Ativo", default=True)
    submit = SubmitField("Salvar")

class FornecedorForm(FlaskForm):
    nome = StringField('Nome do Fornecedor', validators=[DataRequired()])
    cnpj = StringField('CNPJ')
    submit = SubmitField('Salvar')

class EPIForm(FlaskForm):
    nome = StringField('Nome do Equipamento', validators=[DataRequired()])
    ca = StringField('C.A. (Certificado de Aprovação)')
    fornecedor_id = SelectField('Fornecedor', coerce=int, validators=[Optional()])
    submit = SubmitField('Salvar')

class EPIEntradaForm(FlaskForm):
    epi_id = SelectField('Equipamento (EPI)', coerce=int, validators=[DataRequired()])
    quantidade = IntegerField('Quantidade', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Registrar Entrada')

class EPISaidaForm(FlaskForm):
    epi_id = SelectField('Equipamento (EPI)', coerce=int, validators=[DataRequired(message="Selecione um EPI.")])
    quantidade = IntegerField('Quantidade', validators=[DataRequired(message="Informe a quantidade."), NumberRange(min=1)])
    employee_id = SelectField('Funcionário (Cadastrado)', coerce=int, validators=[Optional()])
    retirado_por_terceiro = StringField('Nome (Terceiro/Não cadastrado)')
    submit = SubmitField('Registrar Retirada e Gerar PDF')

class ServicoForm(FlaskForm):
    nome = StringField('Nome do Serviço', validators=[DataRequired(message="O nome do serviço é obrigatório.")])
    submit = SubmitField('Salvar')

# --- NOVO FORMULÁRIO DE AGENDAMENTO ---
class AgendamentoForm(FlaskForm):
    customer_id = SelectField('Cliente', coerce=int, validators=[DataRequired(message="É preciso selecionar um cliente.")])
    servico_id = SelectField('Serviço', coerce=int, validators=[DataRequired(message="É preciso selecionar um serviço.")])
    data_hora = DateTimeField('Data e Hora', format='%Y-%m-%dT%H:%M', validators=[DataRequired(message="A data e hora são obrigatórias.")])
    local = StringField('Local da Coleta/Serviço', validators=[DataRequired(message="O local é obrigatório.")])
    observacao = TextAreaField('Observações')
    status = SelectField('Status', choices=[('Agendado', 'Agendado'), ('Realizado', 'Realizado'), ('Cancelado', 'Cancelado')], default='Agendado')
    submit = SubmitField('Salvar Agendamento')