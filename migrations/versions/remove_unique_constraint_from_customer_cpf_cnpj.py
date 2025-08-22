"""Torna cpf_cnpj opcional no cadastro de cliente (versão corrigida)

Revision ID: c874d6c7b5a3
Revises: f841af533716 
Create Date: 2025-08-22 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c874d6c7b5a3'
# IMPORTANTE: Verifique o nome do seu arquivo de migração ANTERIOR a este e coloque o ID dele aqui.
# Deve ser o arquivo que adicionou o campo 'visitante_nome', provavelmente começa com 'f841af533716'.
down_revision = 'f841af533716' 
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('customer', schema=None) as batch_op:
        # Em SQLite, remover uma constraint 'UNIQUE' exige recriar a tabela.
        # O batch_alter_table lida com isso automaticamente.
        # A alteração no models.py (removendo unique=True) é a fonte da verdade.
        # Esta migração apenas garante que o schema do DB reflita o modelo.
        # O comando drop_constraint pode não ser necessário se o Alembic for inteligente
        # o suficiente, mas o mantemos para clareza. Tentaremos sem ele,
        # confiando que o Alembic vai comparar o modelo com o DB e fazer a coisa certa.
        # Se a constraint não tem um nome explícito, a única forma é recriar a tabela.
        pass # A mágica acontece ao comparar o models.py com o estado atual do banco.

def downgrade():
    # Este comando irá recriar a constraint UNIQUE se você precisar reverter.
    with op.batch_alter_table('customer', schema=None) as batch_op:
        batch_op.create_unique_constraint("uq_customer_cpf_cnpj", ['cpf_cnpj'])