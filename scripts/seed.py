"""Insert the same small, connected salon dataset on every run."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import EstadoCita
from app.infrastructure.database import SessionLocal
from app.infrastructure.models import (
    CitaORM,
    ClienteORM,
    ProfesionalORM,
    ProfesionalServicioORM,
    ReservaORM,
    ServicioORM,
)

SEED_PREFIX = "[SEED]"


def _ensure_cliente(db: Session, nombre: str, email: str, telefono: str) -> ClienteORM:
    cliente = db.scalar(select(ClienteORM).where(ClienteORM.email == email))
    if cliente is None:
        cliente = ClienteORM(
            nombre=nombre,
            email=email,
            telefono=telefono,
            activo=True,
        )
        db.add(cliente)
    return cliente


def _ensure_servicio(
    db: Session,
    nombre: str,
    descripcion: str,
    duracion_minutos: int,
    precio: Decimal,
) -> ServicioORM:
    servicio = db.scalar(select(ServicioORM).where(ServicioORM.nombre == nombre))
    if servicio is None:
        servicio = ServicioORM(
            nombre=nombre,
            descripcion=descripcion,
            duracion_minutos=duracion_minutos,
            precio=precio,
            activo=True,
        )
        db.add(servicio)
    return servicio


def _ensure_profesional(
    db: Session, nombre: str, especialidad: str, email: str, telefono: str
) -> ProfesionalORM:
    profesional = db.scalar(
        select(ProfesionalORM).where(ProfesionalORM.email == email)
    )
    if profesional is None:
        profesional = ProfesionalORM(
            nombre=nombre,
            especialidad=especialidad,
            email=email,
            telefono=telefono,
            activo=True,
        )
        db.add(profesional)
    return profesional


def seed_data(db: Session) -> dict[str, int]:
    """Ensure two clients, services and professionals plus linked bookings."""
    try:
        seeded_appointments = db.scalars(
            select(CitaORM).where(CitaORM.motivo.like(f"{SEED_PREFIX}%"))
        ).all()
        reservation_ids = [appointment.reserva_id for appointment in seeded_appointments]
        for appointment in seeded_appointments:
            db.delete(appointment)
        db.flush()
        for reservation_id in reservation_ids:
            reservation = db.get(ReservaORM, reservation_id)
            if reservation is not None:
                db.delete(reservation)
        db.flush()

        clients = [
            _ensure_cliente(
                db, "Cliente Demo Uno", "seed.cliente1@example.test", "911111111"
            ),
            _ensure_cliente(
                db, "Cliente Demo Dos", "seed.cliente2@example.test", "922222222"
            ),
        ]
        services = [
            _ensure_servicio(
                db, "Servicio Demo Corte", "Corte de cabello", 45, Decimal("12000")
            ),
            _ensure_servicio(
                db, "Servicio Demo Manicure", "Manicure tradicional", 60, Decimal("15000")
            ),
        ]
        professionals = [
            _ensure_profesional(
                db,
                "Profesional Demo Uno",
                "Peluquería",
                "seed.profesional1@example.test",
                "933333333",
            ),
            _ensure_profesional(
                db,
                "Profesional Demo Dos",
                "Manicure",
                "seed.profesional2@example.test",
                "944444444",
            ),
        ]
        db.flush()

        assignments: list[ProfesionalServicioORM] = []
        for professional, service in zip(professionals, services, strict=True):
            assignment = db.scalar(
                select(ProfesionalServicioORM).where(
                    ProfesionalServicioORM.profesional_id == professional.id,
                    ProfesionalServicioORM.servicio_id == service.id,
                )
            )
            if assignment is None:
                assignment = ProfesionalServicioORM(
                    profesional_id=professional.id,
                    servicio_id=service.id,
                )
                db.add(assignment)
            assignments.append(assignment)
        db.flush()

        first_day = datetime.now(timezone.utc) + timedelta(days=7)
        for index, (cliente, assignment) in enumerate(
            zip(clients, assignments, strict=True), start=1
        ):
            reservation = ReservaORM(
                cliente_id=cliente.id,
                profesional_servicio_id=assignment.id,
            )
            db.add(reservation)
            db.flush()
            db.add(
                CitaORM(
                    reserva_id=reservation.id,
                    fecha_hora=first_day + timedelta(days=index),
                    motivo=f"{SEED_PREFIX} cita de demostración {index}",
                    estado=EstadoCita.PENDIENTE,
                )
            )

        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "clientes": len(clients),
        "servicios": len(services),
        "profesionales": len(professionals),
        "profesional_servicios": len(assignments),
        "reservas": len(clients),
        "citas": len(clients),
    }


def main() -> None:
    with SessionLocal() as db:
        counts = seed_data(db)
    print("Seeder ejecutado de forma idempotente:")
    for entity, count in counts.items():
        print(f"- {entity}: {count}")


if __name__ == "__main__":
    main()
