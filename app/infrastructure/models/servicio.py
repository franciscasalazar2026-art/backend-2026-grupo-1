
from decimal import Decimal

from sqlalchemy import Boolean, Integer, Numeric, String, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base


class ServicioORM(Base):
    __tablename__ = "servicios"

    __table_args__ = (
        CheckConstraint(
            "duracion_minutos > 0",
            name="ck_servicios_duracion_positiva"
        ),
        CheckConstraint(
            "precio >= 0",
            name="ck_servicios_precio_no_negativo"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    nombre: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    descripcion: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    duracion_minutos: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    precio: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )

    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    citas: Mapped[list["CitaORM"]] = relationship(
        "CitaORM",
        back_populates="servicio"
    )
