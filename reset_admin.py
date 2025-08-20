# reset_admin.py
import os
from dotenv import load_dotenv
from app import create_app, db
from models import User
from werkzeug.security import generate_password_hash

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Cria uma instância da aplicação Flask
# Isso garante que estamos usando a mesma configuração do app principal
app = create_app()

# 'with app.app_context()' garante que temos acesso ao banco de dados
with app.app_context():
    # Procura pelo usuário 'admin' no banco de dados
    user = User.query.filter_by(username='admin').first()

    # Se o usuário for encontrado, redefine a senha
    if user:
        print(f"Usuário '{user.username}' encontrado.")
        
        # Define a nova senha. Pode trocar '1234' se quiser.
        new_password = '1234'
        user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
        
        # Salva a alteração no banco de dados
        db.session.commit()
        
        print(f"Senha do usuário 'admin' foi redefinida com sucesso para: {new_password}")
    else:
        # Se não encontrar, avisa o usuário
        print("ERRO: Usuário 'admin' não foi encontrado no banco de dados.")
        print("Por favor, apague a pasta 'instance' e refaça o Passo 5 do guia para criar o banco e o usuário.")
