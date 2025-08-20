"""Create cash_movement table for PDV

Revision ID: pdv_cash_20250811152802
Revises: 
Create Date: 2025-08-11 15:28:02
"""

from alembic import op
import sqlalchemy as sa

# migrations/versions/pdv_cash_20250811152802.py
# ...
# revision identifiers, used by Alembic.
revision = 'pdv_cash_20250811152802'
down_revision = 'd9a8413e3fdb' # <--- CORREÇÃO AQUI
branch_labels = None
depends_on = None
# ...

def upgrade():
    op.create_table(
        'cash_movement',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tipo', sa.String(length=20), nullable=False),
        sa.Column('valor', sa.Numeric(10,2), nullable=False),
        sa.Column('pagamento', sa.String(length=20), nullable=False),
        sa.Column('descricao', sa.String(length=255), nullable=True),
        sa.Column('ticket_ref', sa.String(length=50), nullable=True),
        sa.Column('cliente', sa.String(length=120), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
    )

def downgrade():
    op.drop_table('cash_movement')
