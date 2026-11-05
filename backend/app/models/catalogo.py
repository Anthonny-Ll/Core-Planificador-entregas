"""Catálogo académico que administra el admin: carreras, asignaturas, progresos y períodos."""
from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Carrera(Base):
    __tablename__ = "carreras"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(10), unique=True)
    nombre: Mapped[str] = mapped_column(String(100))

    asignaturas: Mapped[list["Asignatura"]] = relationship(back_populates="carrera")


class Asignatura(Base):
    __tablename__ = "asignaturas"

    id: Mapped[int] = mapped_column(primary_key=True)
    carrera_id: Mapped[int] = mapped_column(ForeignKey("carreras.id"))
    codigo: Mapped[str] = mapped_column(String(10), unique=True)  # formato AAAA9999
    nombre: Mapped[str] = mapped_column(String(100))
    creditos: Mapped[int] = mapped_column(Integer, default=1)
    escala: Mapped[float] = mapped_column(Float, default=10)

    carrera: Mapped[Carrera] = relationship(back_populates="asignaturas")
    progresos: Mapped[list["Progreso"]] = relationship(
        back_populates="asignatura", cascade="all, delete-orphan", order_by="Progreso.numero"
    )


class Progreso(Base):
    """Cada asignatura tiene 3 progresos (parciales); sus pesos suman 100."""

    __tablename__ = "progresos"
    __table_args__ = (UniqueConstraint("asignatura_id", "numero"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    asignatura_id: Mapped[int] = mapped_column(ForeignKey("asignaturas.id", ondelete="CASCADE"))
    numero: Mapped[int] = mapped_column(Integer)  # 1, 2 o 3
    peso: Mapped[float] = mapped_column(Float)  # % de la nota final

    asignatura: Mapped[Asignatura] = relationship(back_populates="progresos")


class Periodo(Base):
    __tablename__ = "periodos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(20), unique=True)  # ej. 2026-2
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date] = mapped_column(Date)
    activo: Mapped[bool] = mapped_column(Boolean, default=False)
