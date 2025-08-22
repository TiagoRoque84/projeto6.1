# blueprints/holerites/routes.py
import os
import shutil
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from . import holerites_bp
# --- CORREÇÃO AQUI: Adiciona 'db' à importação ---
from models import db, Employee, EmployeeDocument
from notifications import send_email
from utils import admin_required
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter

HOLERITES_PENDENTES_DIR = "holerites"
HOLERITES_ENVIADOS_DIR = os.path.join("holerites", "enviados")

def get_full_path(subdir):
    return os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'], subdir)

@holerites_bp.route('/')
@login_required
@admin_required
def index():
    pendentes_path = get_full_path(HOLERITES_PENDENTES_DIR)
    os.makedirs(pendentes_path, exist_ok=True) 
    
    arquivos_pendentes = [f for f in os.listdir(pendentes_path) if f.lower().endswith('.pdf')]
    return render_template('holerites/index.html', arquivos=arquivos_pendentes)

@holerites_bp.route('/dividir', methods=['POST'])
@login_required
@admin_required
def dividir_pdf():
    if 'holerite_file' not in request.files:
        flash('Nenhum arquivo enviado.', 'danger')
        return redirect(url_for('holerites.index'))
    
    file = request.files['holerite_file']

    if file.filename == '':
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('holerites.index'))

    if file and file.filename.lower().endswith('.pdf'):
        try:
            pendentes_path = get_full_path(HOLERITES_PENDENTES_DIR)
            reader = PdfReader(file)
            num_pages = len(reader.pages)

            for i in range(num_pages):
                writer = PdfWriter()
                writer.add_page(reader.pages[i])
                
                output_filename = f"holerite_pagina_{i + 1}.pdf"
                output_path = os.path.join(pendentes_path, output_filename)

                with open(output_path, "wb") as output_pdf:
                    writer.write(output_pdf)
            
            flash(f"Sucesso! O arquivo foi dividido em {num_pages} holerites individuais. Agora, renomeie cada arquivo com o nome do respectivo funcionário.", 'success')

        except Exception as e:
            flash(f"Ocorreu um erro ao processar o PDF: {e}", "danger")
    else:
        flash('Por favor, envie um arquivo no formato PDF.', 'danger')

    return redirect(url_for('holerites.index'))

@holerites_bp.route('/distribuir', methods=['POST'])
@login_required
@admin_required
def distribuir():
    pendentes_path = get_full_path(HOLERITES_PENDENTES_DIR)
    enviados_path = get_full_path(HOLERITES_ENVIADOS_DIR)
    os.makedirs(enviados_path, exist_ok=True)

    arquivos_pendentes = [f for f in os.listdir(pendentes_path) if f.lower().endswith('.pdf')]
    
    if not arquivos_pendentes:
        flash("Nenhum holerite encontrado na pasta para envio.", "warning")
        return redirect(url_for('holerites.index'))

    sucessos = 0
    falhas = []

    for nome_arquivo in arquivos_pendentes:
        nome_funcionario = os.path.splitext(nome_arquivo)[0]
        
        funcionario = Employee.query.filter(Employee.nome.ilike(nome_funcionario)).first()

        if not funcionario:
            falhas.append(f"Funcionário '{nome_funcionario}' não encontrado no sistema.")
            continue
        
        if not funcionario.email:
            falhas.append(f"Funcionário '{nome_funcionario}' não possui e-mail cadastrado.")
            continue

        caminho_completo_arquivo = os.path.join(pendentes_path, nome_arquivo)
        assunto = "Seu Holerite está Disponível"
        corpo = f"Olá, {funcionario.nome}.\n\nSeu holerite está em anexo.\n\nAtenciosamente,\nEmpresa."
        
        sucesso, msg_erro = send_email(
            to_list=[funcionario.email],
            subject=assunto,
            body=corpo,
            attachment_path=caminho_completo_arquivo,
            attachment_filename=nome_arquivo
        )

        if sucesso:
            sucessos += 1
            
            try:
                subdir_destino = "func_docs"
                destino_path = get_full_path(subdir_destino)
                os.makedirs(destino_path, exist_ok=True)
                
                shutil.copy(caminho_completo_arquivo, os.path.join(destino_path, nome_arquivo))
                
                novo_documento = EmployeeDocument(
                    employee_id=funcionario.id,
                    tipo="Holerite",
                    descricao=f"Holerite referente ao arquivo {nome_arquivo}",
                    arquivo_path=os.path.join(subdir_destino, nome_arquivo).replace("\\", "/")
                )
                db.session.add(novo_documento)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                falhas.append(f"Falha ao salvar cópia do holerite para '{nome_funcionario}': {e}")

            os.rename(caminho_completo_arquivo, os.path.join(enviados_path, nome_arquivo))
        else:
            falhas.append(f"Falha ao enviar para '{nome_funcionario}': {msg_erro}")

    flash(f"{sucessos} holerite(s) enviado(s) com sucesso!", "success")
    if falhas:
        erros_str = "<br>".join(falhas)
        flash(f"Ocorreram {len(falhas)} falhas:<br>{erros_str}", "danger")

    return redirect(url_for('holerites.index'))