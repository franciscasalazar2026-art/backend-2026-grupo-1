from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base


class DetalleReservaORM(Base):
    __tablename__ = "detalle_reservas"

    __table_args__ = (
        CheckConstraint(
            "duracion_minutos > 0",
            name="ck_detalle_reservas_duracion_positiva",
        ),
        CheckConstraint(
            "precio >= 0",
            name="ck_detalle_reservas_precio_no_negativo",
        ),
        UniqueConstraint(
            "reserva_id",
            "profesional_servicio_id",
            name="uq_detalle_reserva_profesional_servicio",
        ),
        Index("ix_detalle_reservas_reserva_id", "reserva_id"),
        Index(
            "ix_detalle_reservas_profesional_servicio_id",
            "profesional_servicio_id",
        ),
        Index(
            "ix_detalle_reservas_fecha_hora_inicio",
            "fecha_hora_inicio",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    reserva_id: Mapped[int] = mapped_column(
        ForeignKey("reservas.id", ondelete="CASCADE"),
        nullable=False,
    )

    profesional_servicio_id: Mapped[int] = mapped_column(
        ForeignKey("profesional_servicios.id"),
        nullable=False,
    )

    fecha_hora_inicio: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    duracion_minutos: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    precio: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    reserva: Mapped["ReservaORM"] = relationship(
        "ReservaORM",
        back_populates="detalles",
    )

    profesional_servicio: Mapped[
        "ProfesionalServicioORM"
    ] = relationship(
        "ProfesionalServicioORM",
        back_populates="detalles",
    )
