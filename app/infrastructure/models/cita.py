
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models import EstadoCita
from app.infrastructure.database import Base


class CitaORM(Base):
    __tablename__ = "citas"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id"),
        nullable=False,
        index=True,
    )

    servicio_id: Mapped[int] = mapped_column(
        ForeignKey("servicios.id"),
        nullable=False,
        index=True,
    )

    profesional_id: Mapped[int] = mapped_column(
        ForeignKey("profesionales.id"),
        nullable=False,
        index=True,
    )

    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    motivo: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    estado: Mapped[EstadoCita] = mapped_column(
        SQLAlchemyEnum(
            EstadoCita,
            name="estado_cita",
            native_enum=False,
            values_callable=lambda enum_cls: [
                estado.value for estado in enum_cls
            ],
        ),
        nullable=False,
        default=EstadoCita.PENDIENTE,
    )

    cliente: Mapped["ClienteORM"] = relationship(
        "ClienteORM",
        back_populates="citas",
    )

    servicio: Mapped["ServicioORM"] = relationship(
        "ServicioORM",
        back_populates="citas",
    )

    profesional: Mapped["ProfesionalORM"] = relationship(
        "ProfesionalORM",
        back_populates="citas",
    )
