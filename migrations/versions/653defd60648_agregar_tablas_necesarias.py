"""Agregar tablas necesarias

Revision ID: 653defd60648
Revises: 
Create Date: 2025-05-03 23:02:13.445303

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '653defd60648'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('paciente',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nombres', sa.String(length=100), nullable=False),
    sa.Column('apellidos', sa.String(length=100), nullable=False),
    sa.Column('tipo_documento', sa.String(length=20), nullable=True),
    sa.Column('documento', sa.String(length=20), nullable=True),
    sa.Column('fecha_nacimiento', sa.Date(), nullable=True),
    sa.Column('edad', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=100), nullable=True),
    sa.Column('telefono', sa.String(length=20), nullable=False),
    sa.Column('genero', sa.String(length=20), nullable=True),
    sa.Column('estado_civil', sa.String(length=20), nullable=True),
    sa.Column('direccion', sa.String(length=200), nullable=True),
    sa.Column('barrio', sa.String(length=100), nullable=True),
    sa.Column('municipio', sa.String(length=100), nullable=True),
    sa.Column('departamento', sa.String(length=100), nullable=True),
    sa.Column('aseguradora', sa.String(length=100), nullable=True),
    sa.Column('tipo_vinculacion', sa.String(length=50), nullable=True),
    sa.Column('ocupacion', sa.String(length=100), nullable=True),
    sa.Column('referido_por', sa.String(length=100), nullable=True),
    sa.Column('nombre_responsable', sa.String(length=100), nullable=True),
    sa.Column('telefono_responsable', sa.String(length=20), nullable=True),
    sa.Column('parentesco', sa.String(length=50), nullable=True),
    sa.Column('motivo_consulta', sa.Text(), nullable=True),
    sa.Column('enfermedad_actual', sa.Text(), nullable=True),
    sa.Column('antecedentes_personales', sa.Text(), nullable=True),
    sa.Column('antecedentes_familiares', sa.Text(), nullable=True),
    sa.Column('antecedentes_quirurgicos', sa.Text(), nullable=True),
    sa.Column('antecedentes_hemorragicos', sa.Text(), nullable=True),
    sa.Column('farmacologicos', sa.Text(), nullable=True),
    sa.Column('reaccion_medicamentos', sa.Text(), nullable=True),
    sa.Column('alergias', sa.Text(), nullable=True),
    sa.Column('habitos', sa.Text(), nullable=True),
    sa.Column('cepillado', sa.Text(), nullable=True),
    sa.Column('examen_fisico', sa.Text(), nullable=True),
    sa.Column('ultima_visita_odontologo', sa.Text(), nullable=True),
    sa.Column('plan_tratamiento', sa.Text(), nullable=True),
    sa.Column('imagen_1', sa.String(length=200), nullable=True),
    sa.Column('imagen_2', sa.String(length=200), nullable=True),
    sa.Column('dentigrama_canvas', sa.String(length=200), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('cita',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('paciente_id', sa.Integer(), nullable=False),
    sa.Column('fecha', sa.Date(), nullable=False),
    sa.Column('hora', sa.Time(), nullable=False),
    sa.Column('motivo', sa.String(length=255), nullable=True),
    sa.Column('doctor', sa.String(length=100), nullable=False),
    sa.ForeignKeyConstraint(['paciente_id'], ['paciente.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('evolucion',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('descripcion', sa.Text(), nullable=False),
    sa.Column('fecha', sa.DateTime(), nullable=True),
    sa.Column('paciente_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['paciente_id'], ['paciente.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('evolucion')
    op.drop_table('cita')
    op.drop_table('paciente')
    # ### end Alembic commands ###
