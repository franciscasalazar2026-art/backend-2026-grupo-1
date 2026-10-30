"""Agregar detalles para reservas con multiples servicios.

Revision ID: ab54684a0718
Revises: 8a279c14774e
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ab54684a0718"
down_revision: Union[str, Sequence[str], None] = "8a279c14774e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "detalle_reservas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reserva_id", sa.Integer(), nullable=False),
        sa.Column("profesional_servicio_id", sa.Integer(), nullable=False),
        sa.Column("fecha_hora_inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duracion_minutos", sa.Integer(), nullable=False),
        sa.Column("precio", sa.Numeric(10, 2), nullable=False),
        sa.CheckConstraint(
            "duracion_minutos > 0",
            name="ck_detalle_reservas_duracion_positiva",
        ),
        sa.CheckConstraint(
            "precio >= 0",
            name="ck_detalle_reservas_precio_no_negativo",
        ),
        sa.ForeignKeyConstraint(
            ["reserva_id"],
            ["reservas.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["profesional_servicio_id"],
            ["profesional_servicios.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_detalle_reservas_fecha_hora_inicio",
        "detalle_reservas",
        ["fecha_hora_inicio"],
    )
    op.create_index(
        "ix_detalle_reservas_profesional_servicio_id",
        "detalle_reservas",
        ["profesional_servicio_id"],
    )
    op.create_index(
        "ix_detalle_reservas_reserva_id",
        "detalle_reservas",
        ["reserva_id"],
    )

    # Copiar los servicios de las reservas existentes antes de quitar
    # la columna antigua. Si no hay cita, utilizar fecha_creacion.
    # El precio y la duracion corresponden al catalogo actual,
    # ya que el modelo anterior no guardaba una copia historica.
    op.execute(
        sa.text("""
            INSERT INTO detalle_reservas (
                reserva_id,
                profesional_servicio_id,
                fecha_hora_inicio,
                duracion_minutos,
                precio
            )
            SELECT
                r.id,
                r.profesional_servicio_id,
                COALESCE(c.fecha_hora, r.fecha_creacion),
                s.duracion_minutos,
                s.precio
            FROM reservas AS r
            JOIN profesional_servicios AS ps
                ON ps.id = r.profesional_servicio_id
            JOIN servicios AS s
                ON s.id = ps.servicio_id
            LEFT JOIN citas AS c
                ON c.reserva_id = r.id
        """)
    )

    # Eliminar la relacion antigua solo despues de copiar los datos.
    op.drop_index(
        "ix_reservas_profesional_servicio_id",
        table_name="reservas",
    )
    op.drop_constraint(
        "reservas_profesional_servicio_id_fkey",
        "reservas",
        type_="foreignkey",
    )
    op.drop_column("reservas", "profesional_servicio_id")


def downgrade() -> None:
    conexion = op.get_bind()

    # La estructura anterior solo admite un servicio por reserva.
    # No permitir una reversión que descarte servicios.
    multiples = conexion.execute(
        sa.text("""
            SELECT COUNT(*)
            FROM (
                SELECT reserva_id
                FROM detalle_reservas
                GROUP BY reserva_id
                HAVING COUNT(*) > 1
            ) AS agrupadas
        """)
    ).scalar_one()

    sin_detalle = conexion.execute(
        sa.text("""
            SELECT COUNT(*)
            FROM reservas AS r
            LEFT JOIN detalle_reservas AS d
                ON d.reserva_id = r.id
            WHERE d.id IS NULL
        """)
    ).scalar_one()

    if multiples:
        raise RuntimeError(
            "No se puede revertir: hay reservas con varios servicios. "
            "La estructura anterior solo admite uno."
        )

    if sin_detalle:
        raise RuntimeError(
            "No se puede revertir: hay reservas sin detalles asociados."
        )

    op.add_column(
        "reservas",
        sa.Column(
            "profesional_servicio_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.execute(
        sa.text("""
            UPDATE reservas AS r
            SET profesional_servicio_id = d.profesional_servicio_id
            FROM detalle_reservas AS d
            WHERE d.reserva_id = r.id
        """)
    )

    op.alter_column(
        "reservas",
        "profesional_servicio_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.create_foreign_key(
        "reservas_profesional_servicio_id_fkey",
        "reservas",
        "profesional_servicios",
        ["profesional_servicio_id"],
        ["id"],
    )

    op.create_index(
        "ix_reservas_profesional_servicio_id",
        "reservas",
        ["profesional_servicio_id"],
    )

    op.drop_index(
        "ix_detalle_reservas_reserva_id",
        table_name="detalle_reservas",
    )
    op.drop_index(
        "ix_detalle_reservas_profesional_servicio_id",
        table_name="detalle_reservas",
    )
    op.drop_index(
        "ix_detalle_reservas_fecha_hora_inicio",
        table_name="detalle_reservas",
    )
    op.drop_table("detalle_reservas")
