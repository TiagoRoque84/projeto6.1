# blueprints/holerites/routes.py
import os
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from . import holerites_bp
from models import Employee
from notifications import send_email
from utils import admin_required

# Caminhos para as pastas de holerites
HOLERITES_PENDENTES_DIR = "holerites"
HOLERITES_ENVIADOS_DIR = os.path.join("holerites", "enviados")

def get_full_path(subdir):
    return os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'], subdir)

@holerites_bp.route('/')
@login_required
@admin_required
def index():
    """Mostra a tela de distribuição de holerites."""
    pendentes_path = get_full_path(HOLERITES_PENDENTES_DIR)
    os.makedirs(pendentes_path, exist_ok=True) # Garante que a pasta exista
    
    arquivos_pendentes = [f for f in os.listdir(pendentes_path) if f.lower().endswith('.pdf')]
    return render_template('holerites/index.html', arquivos=arquivos_pendentes)

@holerites_bp.route('/distribuir', methods=['POST'])
@login_required
@admin_required
def distribuir():
    """Processa e envia os holerites por e-mail."""
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
        # Extrai o nome do funcionário do nome do arquivo
        nome_funcionario = os.path.splitext(nome_arquivo)[0]
        
        # Procura o funcionário no banco de dados
        funcionario = Employee.query.filter(Employee.nome.ilike(nome_funcionario)).first()

        if not funcionario:
            falhas.append(f"Funcionário '{nome_funcionario}' não encontrado no sistema.")
            continue
        
        if not funcionario.email:
            falhas.append(f"Funcionário '{nome_funcionario}' não possui e-mail cadastrado.")
            continue

        # Monta e envia o e-mail
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
            # Move o arquivo para a pasta de enviados
            os.rename(caminho_completo_arquivo, os.path.join(enviados_path, nome_arquivo))
        else:
            falhas.append(f"Falha ao enviar para '{nome_funcionario}': {msg_erro}")

    # Exibe o resultado
    flash(f"{sucessos} holerite(s) enviado(s) com sucesso!", "success")
    if falhas:
        # Junta todas as falhas em uma única mensagem para não poluir a tela
        erros_str = "<br>".join(falhas)
        flash(f"Ocorreram {len(falhas)} falhas:<br>{erros_str}", "danger")

    return redirect(url_for('holerites.index'))