"""Forma del JSON que entra y sale de la API (Pydantic).

Aquí solo se revisan los TIPOS (que un peso sea número, una fecha sea fecha...).
Las reglas de negocio están en services/validaciones.py.
"""
from datetime import date

from pydantic import BaseModel, ConfigDict


class Salida(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Autenticación ----------
class LoginIn(BaseModel):
    correo: str
    password: str


class RegistroIn(BaseModel):
    nombre: str
    correo: str
    password: str


class UsuarioOut(Salida):
    id: int
    nombre: str
    correo: str
    rol: str
    activo: bool


class TokenOut(BaseModel):
    token: str
    usuario: UsuarioOut


# ---------- Catálogo (admin) ----------
class CarreraIn(BaseModel):
    codigo: str
    nombre: str


class CarreraOut(Salida):
    id: int
    codigo: str
    nombre: str


class ProgresoOut(Salida):
    id: int
    numero: int
    peso: float


class AsignaturaIn(BaseModel):
    carrera_id: int
    codigo: str
    nombre: str
    creditos: int
    escala: float = 10
    pesos: list[float]  # [P1, P2, P3]


class AsignaturaOut(Salida):
    id: int
    carrera_id: int
    codigo: str
    nombre: str
    creditos: int
    escala: float
    carrera: CarreraOut
    progresos: list[ProgresoOut]


class PeriodoIn(BaseModel):
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    activo: bool = False


class PeriodoOut(Salida):
    id: int
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    activo: bool


class EstadoUsuarioIn(BaseModel):
    activo: bool


# ---------- Estudiante ----------
class InscripcionIn(BaseModel):
    periodo_id: int
    asignatura_id: int
    nota_meta: float | None = None
    color: str = "#1f6feb"


class AsignaturaCorta(Salida):
    id: int
    codigo: str
    nombre: str
    creditos: int
    escala: float


class InscripcionOut(Salida):
    id: int
    color: str
    nota_meta: float | None
    asignatura: AsignaturaCorta
    periodo: PeriodoOut


class ProgresoCargaOut(BaseModel):
    """Progreso con cuánto peso de entregas ya tiene cargado (ej. 60/100)."""

    id: int
    numero: int
    peso: float
    cargado: float


class EntregaIn(BaseModel):
    inscripcion_id: int
    progreso_id: int
    titulo: str
    tipo: str
    peso: float
    horas_estimadas: float
    fecha_estimada: date | None = None


class EntregaOut(Salida):
    id: int
    inscripcion_id: int
    progreso_id: int
    titulo: str
    tipo: str
    peso: float
    horas_estimadas: float
    fecha_estimada: date | None
    estado: str
    progreso: ProgresoOut
    peso_final: float  # % de la nota final = peso × peso del progreso / 100
