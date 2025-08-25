# pdf_reports.py

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from datetime import date as _date, date
import os
from decimal import Decimal
from collections import defaultdict

styles = getSampleStyleSheet()
H1 = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=16, spaceAfter=8)
H2 = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=12, spaceAfter=6)
N = styles['Normal']
BodyRight = ParagraphStyle('BodyRight', parent=styles['Normal'], alignment=2) # 2 = RIGHT
Centered = ParagraphStyle('Centered', parent=styles['Normal'], alignment=1) # 1 = CENTER

def _s(v):
    return "" if v is None else str(v)

def P(v, style=N):
    return Paragraph(_s(v), style)

def format_date(d):
    """Formata datas para o padrão DD/MM/YYYY."""
    if d:
        return d.strftime('%d/%m/%Y')
    return ""

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
    title = Paragraph(f"Ficha do Colaborador - {e.nome}", H1)

    photo_flow = None
    if getattr(e, 'foto_path', None):
        try:
            photo_abs = _abs_upload_path(app, e.foto_path)
            if photo_abs and os.path.exists(photo_abs):
                photo_flow = Image(photo_abs, width=3.0*cm, height=4.0*cm)
        except Exception:
            photo_flow = None

    header = Table([[title, photo_flow]], colWidths=[13.0*cm, 4.0*cm])
    header.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP')]))
    elems.extend([header, Spacer(1, 0.3*cm)])

    data = [
        ["Nome", P(e.nome), "Empresa", P(e.company.razao_social if e.company else "")],
        ["Função", P(e.funcao.nome if e.funcao else ""), "Ativo", P("Sim" if e.ativo else "Não")],
        ["CPF", P(e.cpf), "RG", P(e.rg)],
        ["Nascimento", P(format_date(e.data_nascimento)), "Gênero", P(e.genero)],
        ["Estado civil", P(e.estado_civil), "Admissão", P(format_date(e.data_admissao))],
        ["Salário (R$)", P(e.salario), "Jornada", P(e.jornada)],
        ["Telefone", P(e.fone), "Celular", P(e.celular)],
        ["E-mail", P(e.email), "", ""],
        ["Filho < 14", P("Sim" if getattr(e,'filho_menor14',None) else ("Não" if getattr(e,'filho_menor14',None) is not None else "")),
         "Escolaridade", P(getattr(e,'escolaridade', ""))],
        ["Endereço", P(f"{_s(e.logradouro)}, {_s(e.numero)} {_s(e.complemento)}"), "CEP", P(e.cep)],
        ["Bairro/Cidade/UF", P(f"{_s(e.bairro)} / {_s(e.cidade)} / {_s(e.uf)}"), "", ""],
        ["Banco", P(e.banco), "Agência/Conta", P(f"{_s(e.agencia)} / {_s(e.conta)}")],
        ["Tipo de conta", P(e.tipo_conta), "PIX", P(f"{_s(e.pix_tipo)}: {_s(e.pix_chave)}")],
        ["ASO", P(e.aso_tipo), "Validade", P(format_date(e.aso_validade))],
        ["CNH", P(e.cnh), "CNH Validade", P(format_date(e.cnh_validade))],
        ["Toxicológico", "", "Validade", P(format_date(e.exame_toxico_validade))],
    ]
    table = Table(data, colWidths=[3.2*cm,7.8*cm,3.2*cm,3.8*cm])
    table.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),0.25,colors.grey), ('FONTSIZE',(0,0),(-1,-1),9), ('VALIGN',(0,0),(-1,-1),'TOP')
    ]))
    elems.extend([table, Spacer(1,0.5*cm), Paragraph(f"Gerado em {format_date(_date.today())}", N)])
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
        ('GRID',(0,0),(-1,-1),0.25,colors.grey), ('FONTSIZE',(0,0),(-1,-1),10), ('VALIGN',(0,0),(-1,-1),'TOP')
    ]))
    elems.extend([table, Spacer(1,0.5*cm), Paragraph(f"Gerado em {format_date(_date.today())}", N)])
    doc.build(elems)

# -------------------- LISTA DE DOCUMENTOS --------------------
def documents_pdf(buffer, app, docs, titulo="Documentos"):
    doc=SimpleDocTemplate(buffer,pagesize=A4,leftMargin=1.2*cm,rightMargin=1.2*cm,topMargin=1.2*cm,bottomMargin=1.2*cm)
    elems=[Paragraph(titulo,H1)]
    data=[["Empresa","Tipo","Descrição","Número","Expedição","Vencimento","Dias","Status"]]
    today=date.today()
    for d in docs:
        dias,status="",""
        if d.data_vencimento:
            dv=d.data_vencimento
            dias=(dv-today).days
            if dv<today:status="Vencido"
            elif dias<=30:status="A vencer"
            else:status="Vigente"
        data.append([P(d.company.razao_social if getattr(d,'company',None)else""),P(d.tipo.nome if getattr(d,'tipo',None)else""),P(getattr(d,'descricao',"")),P(getattr(d,'numero',"")),P(format_date(getattr(d,'data_expedicao',None))),P(format_date(getattr(d,'data_vencimento',None))),P(dias),P(status or getattr(d,'status',''))])
    col_widths=[4.0*cm,2.0*cm,5.0*cm,1.6*cm,1.8*cm,1.9*cm,0.9*cm,1.4*cm]
    table=Table(data,colWidths=col_widths,repeatRows=1,hAlign='LEFT')
    table.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.25,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.whitesmoke),('FONTSIZE',(0,0),(-1,-1),9),('VALIGN',(0,0),(-1,-1),'TOP')]))
    elems.append(table)
    doc.build(elems)

# -------------------- LISTA DE TOXICOLÓGICOS --------------------
def toxicos_pdf(buffer, app, items, titulo="Exame Toxicológico"):
    doc=SimpleDocTemplate(buffer,pagesize=A4,leftMargin=1.6*cm,rightMargin=1.6*cm,topMargin=1.2*cm,bottomMargin=1.2*cm)
    elems=[Paragraph(titulo,H1)]
    data=[["Colaborador","Empresa","Validade","Dias","Status"]]
    today=date.today()
    for e in items:
        dias,status="",""
        val=getattr(e,'exame_toxico_validade',None)
        if val:
            dias=(val-today).days
            if val<today:status="Vencido"
            elif dias<=30:status="A vencer"
            else:status="Vigente"
        data.append([P(e.nome),P(e.company.razao_social if getattr(e,'company',None)else""),P(format_date(val)),P(dias),P(status),])
    table=Table(data,colWidths=[5.0*cm,6.0*cm,2.5*cm,1.5*cm,2.0*cm],repeatRows=1,hAlign='LEFT')
    table.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.25,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.whitesmoke),('FONTSIZE',(0,0),(-1,-1),9),('VALIGN',(0,0),(-1,-1),'TOP')]))
    elems.extend([table,Spacer(1,0.4*cm),Paragraph(f"Gerado em {format_date(_date.today())}",N)])
    doc.build(elems)

# -------------------- COMPROVANTE DE RETIRADA DE EPI --------------------
def epi_saida_pdf(buffer, app, saida):
    doc=SimpleDocTemplate(buffer,pagesize=A4,leftMargin=2*cm,rightMargin=2*cm,topMargin=1.5*cm,bottomMargin=1.5*cm)
    elems=[]
    elems.append(Paragraph("Comprovante de Retirada de EPI",H1))
    elems.append(Spacer(1,0.5*cm))
    
    data_retirada=saida.data_saida.strftime('%d/%m/%Y às %H:%M')
    
    items_data = [[P("<b>Equipamento (EPI)</b>"), P("<b>Qtd</b>")]]
    for item in saida.items:
        items_data.append([
            P(f"{_s(item.epi.nome)} (CA: {_s(item.epi.ca)})"),
            P(str(item.quantidade), Centered)
        ])

    items_table = Table(items_data, colWidths=[15*cm, 2*cm])
    items_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
    
    info_data=[
        ["Data da Retirada:", P(data_retirada)],
        ["Itens Retirados:", items_table]
    ]
    info_table=Table(info_data,colWidths=[5*cm,12*cm])
    info_table.setStyle(TableStyle([('FONTSIZE',(0,0),(-1,-1),10),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6),]))
    elems.append(info_table)
    elems.append(Spacer(1,1*cm))
    
    termo_texto="Declaro para os devidos fins que recebi da empresa o(s) equipamento(s) de proteção individual (EPI) descrito(s) acima, em perfeitas condições de uso. Comprometo-me a utilizá-lo(s) durante toda a jornada de trabalho, a zelar pela sua guarda e conservação, e a devolvê-lo(s) quando solicitado. Estou ciente de que o extravio ou dano por uso indevido poderá ser descontado de meu salário, conforme previsto no Art. 462 da CLT."
    elems.append(Paragraph(termo_texto,N))
    elems.append(Spacer(1, 2.5*cm))
    
    assinatura_data=[
        [P("________________________________________", Centered)],
        [P(f"<b>{_s(saida.retirado_por)}</b>", Centered)],
        [P(f"CPF: {_s(saida.employee.cpf if saida.employee else 'Não informado')}", Centered)],
    ]
    assinatura_table = Table(assinatura_data, colWidths=[17*cm])
    assinatura_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 1),
    ]))
    elems.append(assinatura_table)

    elems.append(Spacer(1,2*cm))
    elems.append(Paragraph(f"Gerado em {format_date(_date.today())}",BodyRight))
    doc.build(elems)

# -------------------- RELATÓRIO DIÁRIO DE CAIXA (A4) --------------------
def pdv_summary_pdf(buffer, app, movements, start_date, end_date):
    doc=SimpleDocTemplate(buffer,pagesize=A4,leftMargin=1.5*cm,rightMargin=1.5*cm,topMargin=1.5*cm,bottomMargin=1.5*cm)
    elems=[]
    if start_date==end_date:periodo_str=f"Data: {start_date.strftime('%d/%m/%Y')}"
    else:periodo_str=f"Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}"
    elems.append(Paragraph(f"Relatório de Movimentação de Caixa",H1))
    elems.append(Paragraph(periodo_str,H2))
    elems.append(Spacer(1,0.8*cm))
    table_data=[[P('<b>Hora</b>'),P('<b>Tipo</b>'),P('<b>Descrição/Cliente</b>'),P('<b>Pagamento</b>'),P('<b>Valor (R$)</b>')]]
    totals=defaultdict(Decimal)
    for mov in movements:
        valor=mov.valor or Decimal(0)
        valor_str=f"{valor:.2f}".replace('.',',')
        if mov.tipo in['VENDA','PAGAMENTO']:totals[mov.pagamento]+=valor
        elif mov.tipo in['SANGRIA','RETIRADA']:
            totals[mov.tipo]+=valor
            valor_str=f"-{valor_str}"
        descricao=mov.customer.nome_razao_social if mov.customer else(mov.descricao or'-')
        table_data.append([mov.created_at.strftime('%H:%M:%S'),mov.tipo,descricao,mov.pagamento,Paragraph(valor_str,BodyRight)])
    table=Table(table_data,colWidths=[2*cm,2.5*cm,8*cm,2.5*cm,3*cm])
    table.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(0,0),(-1,-1),'LEFT'),('ALIGN',(4,1),(4,-1),'RIGHT'),]))
    elems.append(table)
    elems.append(Spacer(1,1*cm))
    summary_data=[[P('<b>Resumo do Período</b>'),'']]
    total_entradas=Decimal(0)
    for metodo in['DINHEIRO','PIX','CARTAO','BAIXA']:
        if totals[metodo]>0:
            summary_data.append([f'Entradas em {metodo}:',Paragraph(f"R$ {totals[metodo]:.2f}".replace('.',','),BodyRight)])
            total_entradas+=totals[metodo]
    summary_data.append([P('<b>Total de Entradas:</b>'),Paragraph(f"<b>R$ {total_entradas:.2f}</b>".replace('.',','),BodyRight)])
    summary_data.append(['',''])
    total_saidas=Decimal(0)
    for tipo_saida in['SANGRIA','RETIRADA']:
        if totals[tipo_saida]>0:
            summary_data.append([f'Total de {tipo_saida}:',Paragraph(f"- R$ {totals[tipo_saida]:.2f}".replace('.',','),BodyRight)])
            total_saidas+=totals[tipo_saida]
    summary_data.append([P('<b>Total de Saídas:</b>'),Paragraph(f"<b>- R$ {total_saidas:.2f}</b>".replace('.',','),BodyRight)])
    summary_data.append(['',''])
    saldo_final=total_entradas-total_saidas
    summary_data.append([P('<b>SALDO FINAL:</b>'),Paragraph(f"<b>R$ {saldo_final:.2f}</b>".replace('.',','),BodyRight)])
    summary_table=Table(summary_data,colWidths=[6*cm,4*cm])
    summary_table.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'RIGHT'),('SPAN',(0,0),(1,0)),('ALIGN',(0,0),(0,0),'CENTER'),('FONTNAME',(0,0),(-1,-1),'Helvetica'),('FONTNAME',(0,2),(1,2),'Helvetica-Bold'),('FONTNAME',(0,5),(1,5),'Helvetica-Bold'),('FONTNAME',(0,7),(1,7),'Helvetica-Bold'),('BOX',(0,0),(-1,-1),1,colors.black),('INNERGRID',(0,0),(-1,-1),0.5,colors.grey),]))
    elems.append(summary_table)
    doc.build(elems)

# -------------------- RELATÓRIO DE EPI (A4) --------------------
def epi_summary_pdf(buffer, app, movements, start_date, end_date):
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    elems = []
    
    if start_date == end_date:
        periodo_str = f"Data: {start_date.strftime('%d/%m/%Y')}"
    else:
        periodo_str = f"Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}"

    elems.append(Paragraph("Relatório de Movimentação de EPIs", H1))
    elems.append(Paragraph(periodo_str, H2))
    elems.append(Spacer(1, 0.8*cm))

    table_data = [[P('<b>Data/Hora</b>'), P('<b>EPI</b>'), P('<b>Tipo</b>'), P('<b>Qtd</b>'), P('<b>Recebido por</b>')]]
    
    for mov in movements:
        table_data.append([
            P(mov.data_movimentacao.strftime('%d/%m/%Y %H:%M')),
            P(mov.epi.nome),
            P(mov.tipo),
            P(str(mov.quantidade)),
            P(mov.retirado_por)
        ])

    table = Table(table_data, colWidths=[3.5*cm, 6.5*cm, 2*cm, 1.5*cm, 4.5*cm])
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (3,1), (3,-1), 'CENTER'),
    ]))
    elems.append(table)
    doc.build(elems)

# -------------------- ORÇAMENTO (A4) --------------------
def proposal_pdf(buffer, app, proposal):
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    elems = []
    
    company = proposal.issuing_company
    logo_path = os.path.join(app.root_path, "static", "img", "logo.png")
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=5*cm, height=2.5*cm, hAlign='LEFT')
        elems.append(logo)
        elems.append(Spacer(1, 0.5*cm))

    elems.append(Paragraph("Proposta Comercial", H1))
    elems.append(Spacer(1, 0.5*cm))
    
    customer = proposal.customer
    client_info = f"""
        <b>Cliente:</b> {customer.nome_razao_social}<br/>
    """
    if proposal.attention:
        client_info += f"<b>A/C:</b> {proposal.attention}<br/>"

    elems.append(Paragraph(client_info, N))
    elems.append(Spacer(1, 0.5*cm))

    elems.append(Paragraph("A empresa <b>{}</b>, vem por meio desta, apresentar a proposta para prestação de serviços conforme descrito abaixo:".format(company.nome_fantasia or company.razao_social), N))
    elems.append(Spacer(1, 1*cm))

    item_data = [[P("<b>DESCRIÇÃO DO SERVIÇO</b>"), P("<b>VALOR</b>")]]
    for item in proposal.items:
        valor_str = f"R$ {item.value}"
        if item.unit:
            valor_str += f" (por {item.unit})"
        item_data.append([P(item.description), P(valor_str)])
    
    item_table = Table(item_data, colWidths=[12*cm, 5*cm])
    item_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elems.append(item_table)
    elems.append(Spacer(1, 1*cm))
    
    data_emissao = proposal.created_at.strftime('%d de %B de %Y')
    cidade_emissao = company.cidade or "nossa cidade"
    elems.append(Paragraph(f"{cidade_emissao}, {data_emissao}", N))
    elems.append(Spacer(1, 2.5*cm))

    assinatura_data = [
        [P("____________________________", Centered)],
        [P(f"<b>{proposal.representative_name}</b>", Centered)],
        [P(f"{company.nome_fantasia or company.razao_social}", Centered)],
    ]
    assinatura_table = Table(assinatura_data, colWidths=[17*cm])
    elems.append(assinatura_table)
    
    footer_text = f"<font size='8'>{company.logradouro}, {company.numero} - {company.cidade}/{company.uf} | CNPJ: {company.cnpj}</font>"
    elems.append(Spacer(1, 2*cm))
    elems.append(Paragraph(footer_text, Centered))

    doc.build(elems)