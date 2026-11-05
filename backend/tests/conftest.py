"""Cada prueba de la API usa una base de datos SQLite temporal, nueva y vacía."""
import os
import tempfile

import pytest

# Debe definirse ANTES de importar la app para que use la BD temporal.
_carpeta = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_carpeta}/test.db"
os.environ["ADMIN_PASSWORD"] = "ClaveAdmin1"

from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def cliente():
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as c:  # el lifespan crea las tablas y el seed
        yield c


def _token(cliente, correo, password):
    r = cliente.post("/api/auth/login", json={"correo": correo, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture()
def admin(cliente):
    return _token(cliente, "admin@udla.edu.ec", "ClaveAdmin1")


@pytest.fixture()
def estudiante(cliente):
    return _token(cliente, "estudiante@udla.edu.ec", "Estudiante123")
