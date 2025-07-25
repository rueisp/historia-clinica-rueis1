"""Add observaciones to Cita model

Revision ID: 69940c9b21af
Revises: 1919c834d782
Create Date: 2025-05-11 17:58:34.898307

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '69940c9b21af'
down_revision = '1919c834d782'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('cita', schema=None) as batch_op:
        batch_op.add_column(sa.Column('observaciones', sa.Text(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('cita', schema=None) as batch_op:
        batch_op.drop_column('observaciones')

    # ### end Alembic commands ###
