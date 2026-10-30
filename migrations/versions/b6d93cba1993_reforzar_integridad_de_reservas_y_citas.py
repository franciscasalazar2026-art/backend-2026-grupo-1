"""reforzar integridad de reservas y citas

Revision ID: b6d93cba1993
Revises: ab54684a0718
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b6d93cba1993"
down_revision: Union[str, Sequence[str], None] = "ab54684a0718"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Reemplazar clave foranea de citas con borrado en cascada.
    op.drop_constraint(
        "citas_reserva_id_fkey",
        "citas",
        type_="foreignkey",
    )

    op.create_foreign_key(
        "fk_citas_reserva_id_reservas",
        "citas",
        "reservas",
        ["reserva_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Evitar repetir el mismo profesional-servicio
    # dentro de una misma reserva.
    op.create_unique_constraint(
        "uq_detalle_reserva_profesional_servicio",
        "detalle_reservas",
        ["reserva_id", "profesional_servicio_id"],
    )


def downgrade() -> None:
    # Revertir las restricciones en orden inverso.
    op.drop_constraint(
        "uq_detalle_reserva_profesional_servicio",
        "detalle_reservas",
        type_="unique",
    )

    op.drop_constraint(
        "fk_citas_reserva_id_reservas",
        "citas",
        type_="foreignkey",
    )

    op.create_foreign_key(
        "citas_reserva_id_fkey",
        "citas",
        "reservas",
        ["reserva_id"],
        ["id"],
    )
