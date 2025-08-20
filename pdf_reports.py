from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from datetime import date as _date, date
import os

styles = getSampleStyleSheet()
H1 = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=16, spaceAfter=8)
N = styles['Normal']

def _s(v): 
    return "" if v is None else str(v)

def P(v): 
    return Paragraph(_s(v), N)

def _abs_upload_path(app, rel):
    """Resolve caminho absoluto de algo salvo em uploads/..."""
    if not rel:
        return None
    rel = str(rel).replace('\\', '/').lstrip('/')
    if rel.startswith('uploads/'):
        rel = rel[len('uploads/'):]
    return os.path.join(app.root_path, app.config.get('UPLOAD_FOLDER', 'uploads'), rel)

# -------------------- COLABORADOR (com foto 3x4) --------------------
def employee_pdf(buffer, app, e):
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm, topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    elems=[]
    title = Paragraph(f"Ficha do Colaborador - #{e.id}", H1)

    photo_flow = None
    if getattr(e, 'foto_path', None):
        try:
            photo_abs = _abs_upload_path(app, e.foto_path)
            if photo_abs and os.path.exists(photo_abs):
                photo_flow = Image(photo_abs, width=3.0*cm, height=4.0*cm)  # 3x4 cm
        except Exception:
            photo_flow = None

    header = Table([[title, photo_flow]], colWidths=[13.0*cm, 4.0*cm])
    header.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP')]))
    elems.extend([header, Spacer(1, 0.3*cm)])

    data = [
        ["Nome", P(e.nome), "Empresa", P(e.company.razao_social if e.company else "")],
        ["Função", P(e.funcao.nome if e.funcao else ""), "Ativo", P("Sim" if e.ativo else "Não")],
        ["CPF", P(e.cpf), "RG", P(e.rg)],
        ["Nascimento", P(e.data_nascimento), "Gênero", P(e.genero)],
        ["Estado civil", P(e.estado_civil), "Admissão", P(e.data_admissao)],
        ["Salário (R$)", P(e.salario), "Jornada", P(e.jornada)],
        ["Telefone", P(e.fone), "Celular", P(e.celular)],
        ["E-mail", P(e.email), "", ""],
        ["Filho < 14", P("Sim" if getattr(e,'filho_menor14',None) else ("Não" if getattr(e,'filho_menor14',None) is not None else "")),
         "Escolaridade", P(getattr(e,'escolaridade', ""))],
        ["Endereço", P(f"{_s(e.logradouro)}, {_s(e.numero)} {_s(e.complemento)}"), "CEP", P(e.cep)],
        ["Bairro/Cidade/UF", P(f"{_s(e.bairro)} / {_s(e.cidade)} / {_s(e.uf)}"), "", ""],
        ["Banco", P(e.banco), "Agência/Conta", P(f"{_s(e.agencia)} / {_s(e.conta)}")],
        ["Tipo de conta", P(e.tipo_conta), "PIX", P(f"{_s(e.pix_tipo)}: {_s(e.pix_chave)}")],
        ["ASO", P(e.aso_tipo), "Validade", P(e.aso_validade)],
        ["CNH", P(e.cnh), "CNH Validade", P(e.cnh_validade)],
        ["Toxicológico", "", "Validade", P(e.exame_toxico_validade)],
    ]
    table = Table(data, colWidths=[3.2*cm,7.8*cm,3.2*cm,3.8*cm])
    table.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),0.25,colors.grey),
        ('FONTSIZE',(0,0),(-1,-1),9),
        ('VALIGN',(0,0),(-1,-1),'TOP')
    ]))
    elems.extend([table, Spacer(1,0.5*cm), Paragraph(f"Gerado em {_date.today().strftime('%d/%m/%Y')}", N)])
    doc.build(elems)

# -------------------- EMPRESA --------------------
def company_pdf(buffer, app, c):
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm, topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    elems=[Paragraph(f"Ficha da Empresa - #{c.id}", H1)]
    data = [
        ["Razão Social", P(c.razao_social)],
        ["Nome Fantasia", P(c.nome_fantasia)],
        ["CNPJ", P(c.cnpj)],
        ["Inscrição Estadual", P(c.inscricao_estadual)],
        ["Endereço", P(f"{_s(c.logradouro)}, {_s(c.numero)} {_s(c.complemento)}")],
        ["Bairro/Cidade/UF", P(f"{_s(c.bairro)} / {_s(c.cidade)} / {_s(c.uf)}")],
        ["CEP", P(c.cep)],
        ["Status", P("Ativa" if getattr(c,'ativa',True) else "Inativa")],
        ["Emails alerta", P(getattr(c,'alert_email',""))],
        ["WhatsApp alerta", P(getattr(c,'alert_whatsapp',""))],
    ]
    table = Table(data, colWidths=[5*cm,12*cm])
    table.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),0.25,colors.grey),
        ('FONTSIZE',(0,0),(-1,-1),10),
        ('VALIGN',(0,0),(-1,-1),'TOP')
    ]))
    elems.extend([table, Spacer(1,0.5*cm), Paragraph(f"Gerado em {_date.today().strftime('%d/%m/%Y')}", N)])
    doc.build(elems)

# -------------------- LISTA DE DOCUMENTOS --------------------
def documents_pdf(buffer, app, docs, titulo="Documentos"):
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.2*cm, rightMargin=1.2*cm, topMargin=1.2*cm, bottomMargin=1.2*cm
    )
    elems=[Paragraph(titulo, H1)]
    data=[["Empresa","Tipo","Descrição","Número","Expedição","Vencimento","Dias","Status"]]
    today = date.today()
    for d in docs:
        dias = ""
        status = ""
        if d.data_vencimento:
            dv = d.data_vencimento
            dias = (dv - today).days
            if dv < today:
                status = "Vencido"
            elif dias <= 30:
                status = "A vencer"
            else:
                status = "Vigente"
        data.append([
            P(d.company.razao_social if getattr(d,'company',None) else ""),
            P(d.tipo.nome if getattr(d,'tipo',None) else ""),
            P(getattr(d,'descricao',"")),
            P(getattr(d,'numero',"")),
            P(getattr(d,'data_expedicao',"")),
            P(getattr(d,'data_vencimento',"")),
            P(dias),
            P(status or getattr(d,'status','')),
        ])
    col_widths = [4.0*cm, 2.0*cm, 5.0*cm, 1.6*cm, 1.8*cm, 1.9*cm, 0.9*cm, 1.4*cm]
    table = Table(data, colWidths=col_widths, repeatRows=1, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),0.25,colors.grey),
        ('BACKGROUND',(0,0),(-1,0),colors.whitesmoke),
        ('FONTSIZE',(0,0),(-1,-1),9),
        ('VALIGN',(0,0),(-1,-1),'TOP')
    ]))
    elems.append(table)
    doc.build(elems)

# -------------------- LISTA DE TOXICOLÓGICOS --------------------
def toxicos_pdf(buffer, app, items, titulo="Exame Toxicológico"):
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.6*cm, rightMargin=1.6*cm, topMargin=1.2*cm, bottomMargin=1.2*cm
    )
    elems=[Paragraph(titulo, H1)]
    data=[["Colaborador","Empresa","Validade","Dias","Status"]]
    today = date.today()
    for e in items:
        dias = ""
        status = ""
        val = getattr(e,'exame_toxico_validade',None)
        if val:
            dias = (val - today).days
            if val < today:
                status = "Vencido"
            elif dias <= 30:
                status = "A vencer"
            else:
                status = "Vigente"
        data.append([
            P(e.nome),
            P(e.company.razao_social if getattr(e,'company',None) else ""),
            P(val),
            P(dias),
            P(status),
        ])
    table = Table(data, colWidths=[5.0*cm,6.0*cm,2.5*cm,1.5*cm,2.0*cm], repeatRows=1, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),0.25,colors.grey),
        ('BACKGROUND',(0,0),(-1,0),colors.whitesmoke),
        ('FONTSIZE',(0,0),(-1,-1),9),
        ('VALIGN',(0,0),(-1,-1),'TOP')
    ]))
    elems.extend([table, Spacer(1,0.4*cm), Paragraph(f"Gerado em {_date.today().strftime('%d/%m/%Y')}", N)])
    doc.build(elems)
