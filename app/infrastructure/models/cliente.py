from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base


class ClienteORM(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    nombre: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(254), nullable=False, unique=True, index=True
    )

    telefono: Mapped[str] = mapped_column(
        String(15), nullable=False
    )

    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    reservas: Mapped[list["ReservaORM"]] = relationship(
        "ReservaORM",
        back_populates="cliente",
    )
