from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base


class ReservaORM(Base):
    __tablename__ = "reservas"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id"),
        nullable=False,
        index=True,
    )

    profesional_servicio_id: Mapped[int] = mapped_column(
        ForeignKey("profesional_servicios.id"),
        nullable=False,
        index=True,
    )

    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    cliente: Mapped["ClienteORM"] = relationship(
        "ClienteORM",
        back_populates="reservas",
    )

    profesional_servicio: Mapped["ProfesionalServicioORM"] = relationship(
        "ProfesionalServicioORM",
        back_populates="reservas",
    )

    cita: Mapped[Optional["CitaORM"]] = relationship(
        "CitaORM",
        back_populates="reserva",
        uselist=False,
    )
