"""Datos iniciales: el administrador y un catálogo de ejemplo (solo si la BD está vacía)."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import ADMIN_EMAIL, ADMIN_PASSWORD
from app.core.security import encriptar_password
from app.models import Asignatura, Carrera, Periodo, Progreso, Usuario

CATALOGO = {
    ("ISW", "Ingeniería de Software"): [
        ("ISWZ2105", "Aplicaciones Distribuidas", 3, [30, 30, 40]),
        ("ISWZ3101", "Ingeniería Web", 3, [30, 30, 40]),
        ("ISWZ3204", "Arquitectura de Software", 3, [25, 35, 40]),
        ("ISWZ3310", "Seguridad Informática", 2, [30, 30, 40]),
    ],
    ("ITI", "Tecnologías de la Información"): [
        ("ITIZ3304", "Gestión de TI", 3, [30, 30, 40]),
        ("ITIZ2201", "Análisis y Visualización de Datos", 3, [30, 35, 35]),
    ],
    ("IIA", "Ingeniería en Inteligencia Artificial"): [
        ("IIAZ2101", "Aprendizaje Automático", 4, [30, 30, 40]),
        ("IIAZ1102", "Probabilidad y Estadística", 3, [35, 35, 30]),
    ],
}


def cargar_datos(db: Session) -> None:
    # Administrador global (la contraseña viene de la variable de entorno ADMIN_PASSWORD).
    if not db.scalar(select(Usuario).where(Usuario.rol == "admin")):
        db.add(Usuario(
            nombre="Administrador", correo=ADMIN_EMAIL.lower(),
            password_hash=encriptar_password(ADMIN_PASSWORD), rol="admin",
        ))

    if not db.scalar(select(Carrera)):
        for (codigo, nombre), asignaturas in CATALOGO.items():
            carrera = Carrera(codigo=codigo, nombre=nombre)
            for cod, nom, creditos, pesos in asignaturas:
                carrera.asignaturas.append(Asignatura(
                    codigo=cod, nombre=nom, creditos=creditos, escala=10,
                    progresos=[Progreso(numero=n, peso=p) for n, p in enumerate(pesos, 1)],
                ))
            db.add(carrera)

    if not db.scalar(select(Periodo)):
        db.add_all([
            Periodo(nombre="2026-1", fecha_inicio=date(2026, 3, 2), fecha_fin=date(2026, 7, 31), activo=False),
            Periodo(nombre="2026-2", fecha_inicio=date(2026, 9, 1), fecha_fin=date(2027, 1, 29), activo=True),
        ])

    # Estudiante de prueba para la demo.
    if not db.scalar(select(Usuario).where(Usuario.rol == "estudiante")):
        db.add(Usuario(
            nombre="Estudiante Demo", correo="estudiante@udla.edu.ec",
            password_hash=encriptar_password("Estudiante123"), rol="estudiante",
        ))
    db.commit()
