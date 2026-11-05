"""Punto de entrada del backend: crea la app, la BD y registra los controladores."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.controllers import admin_controller, auth_controller, estudiante_controller
from app.core.config import CORS_ORIGINS
from app.core.database import Base, SessionLocal, engine
from app.seed import cargar_datos

# Carpeta donde Vite deja el build de React (frontend/dist)
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Al arrancar: crea las tablas y carga los datos iniciales si la BD está vacía."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        cargar_datos(db)
    yield


app = FastAPI(title="Planificador de entregas académicas", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, allow_origins=CORS_ORIGINS,
    allow_methods=["*"], allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_controller.router)
app.include_router(admin_controller.router)
app.include_router(estudiante_controller.router)


@app.get("/api/salud", tags=["Sistema"])
def salud():
    """Render usa esta ruta para saber si la app está viva."""
    return {"estado": "ok"}


# En producción (Render) FastAPI también sirve la página de React ya compilada.
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{ruta:path}", include_in_schema=False)
    def frontend(ruta: str):
        """Cualquier ruta que no sea de la API devuelve index.html (React Router decide qué mostrar)."""
        if ruta.startswith("api/"):
            raise HTTPException(404, "Ruta no encontrada")
        archivo = (FRONTEND_DIST / ruta).resolve()
        # is_relative_to evita que alguien pida archivos fuera de dist/ con "../"
        if ruta and archivo.is_relative_to(FRONTEND_DIST.resolve()) and archivo.is_file():
            return FileResponse(archivo)
        return FileResponse(FRONTEND_DIST / "index.html")
