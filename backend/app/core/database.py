"""Conexión a la base de datos SQLite con SQLAlchemy."""
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import DATABASE_URL

# El archivo planificador.db se crea solo dentro de la carpeta backend/.
DB_PATH = Path(__file__).resolve().parent.parent.parent / "planificador.db"
URL = DATABASE_URL or f"sqlite:///{DB_PATH}"

engine = create_engine(URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)


@event.listens_for(engine, "connect")
def activar_claves_foraneas(conexion, _):
    """SQLite no revisa las claves foráneas si no se le pide explícitamente."""
    cursor = conexion.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Base(DeclarativeBase):
    """Clase padre de todas las tablas."""


def get_db():
    """Dependencia de FastAPI: abre una sesión de BD por petición y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
