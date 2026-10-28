from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base


class ProfesionalServicioORM(Base):
    __tablename__ = "profesional_servicios"

    __table_args__ = (
        UniqueConstraint(
            "profesional_id",
            "servicio_id",
            name="uq_profesional_servicio",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    profesional_id: Mapped[int] = mapped_column(
        ForeignKey("profesionales.id"),
        nullable=False,
        index=True,
    )

    servicio_id: Mapped[int] = mapped_column(
        ForeignKey("servicios.id"),
        nullable=False,
        index=True,
    )

    profesional: Mapped["ProfesionalORM"] = relationship(
        "ProfesionalORM",
        back_populates="profesional_servicios",
    )

    servicio: Mapped["ServicioORM"] = relationship(
        "ServicioORM",
        back_populates="profesional_servicios",
    )

    reservas: Mapped[list["ReservaORM"]] = relationship(
        "ReservaORM",
        back_populates="profesional_servicio",
    )
