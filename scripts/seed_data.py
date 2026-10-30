import sys
import os

# Permitir importar módulos desde la raíz del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.infrastructure.models
from app.infrastructure.database import SessionLocal, engine, Base
from app.infrastructure.models import ServicioORM

def poblar_base_de_datos():
    print("Iniciando sembrado de datos iniciales...")

    # Intentar conexión a la BD principal; si falla, usar SQLite local
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
    except Exception:
        print(" [!] PostgreSQL no disponible. Usando base de datos SQLite local para la prueba...")
        sqlite_engine = create_engine("sqlite:///./test_dev.db", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=sqlite_engine)
        SQLiteSession = sessionmaker(autocommit=False, autoflush=False, bind=sqlite_engine)
        db = SQLiteSession()

    try:
        servicios_iniciales = [
            {
                "nombre": "Corte de Cabello Premium",
                "descripcion": "Corte personalizado, lavado profundo y peinado con estilizado",
                "duracion_minutos": 45,
                "precio": 18000.0,
                "activo": True
            },
            {
                "nombre": "Manicure y Esmaltado",
                "descripcion": "Limpieza de uñas, exfoliación y esmaltado permanente",
                "duracion_minutos": 60,
                "precio": 22000.0,
                "activo": True
            },
            {
                "nombre": "Tratamiento Capilar Hidratante",
                "descripcion": "Aplicación de mascarilla de queratina y sellado con calor",
                "duracion_minutos": 50,
                "precio": 28000.0,
                "activo": True
            },
            {
                "nombre": "Pedicure Spa",
                "descripcion": "Tratamiento completo de pies con hidromasaje y exfoliación",
                "duracion_minutos": 60,
                "precio": 25000.0,
                "activo": True
            }
        ]

        for datos_servicio in servicios_iniciales:
            existe = db.query(ServicioORM).filter(ServicioORM.nombre == datos_servicio["nombre"]).first()
            if not existe:
                nuevo_servicio = ServicioORM(**datos_servicio)
                db.add(nuevo_servicio)
                print(f" [+] Servicio agregado: {datos_servicio['nombre']}")
            else:
                print(f" [=] Servicio ya existía: {datos_servicio['nombre']}")

        db.commit()
        print("\n¡Sembrado de datos finalizado con éxito!")

    except Exception as error:
        print(f"Error durante la inserción de datos: {error}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    poblar_base_de_datos()