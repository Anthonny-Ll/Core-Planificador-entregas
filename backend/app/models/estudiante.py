"""Datos de cada estudiante: sus materias inscritas y sus entregas."""
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.catalogo import Asignatura, Periodo, Progreso


class Inscripcion(Base):
    """Una materia que el estudiante cursa en un período."""

    __tablename__ = "inscripciones"
    __table_args__ = (UniqueConstraint("usuario_id", "asignatura_id", "periodo_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    asignatura_id: Mapped[int] = mapped_column(ForeignKey("asignaturas.id"))
    periodo_id: Mapped[int] = mapped_column(ForeignKey("periodos.id"))
    color: Mapped[str] = mapped_column(String(7), default="#1f6feb")
    nota_meta: Mapped[float | None] = mapped_column(Float, nullable=True)

    asignatura: Mapped[Asignatura] = relationship()
    periodo: Mapped[Periodo] = relationship()
    entregas: Mapped[list["Entrega"]] = relationship(
        back_populates="inscripcion", cascade="all, delete-orphan"
    )


class Entrega(Base):
    __tablename__ = "entregas"

    id: Mapped[int] = mapped_column(primary_key=True)
    inscripcion_id: Mapped[int] = mapped_column(ForeignKey("inscripciones.id", ondelete="CASCADE"))
    progreso_id: Mapped[int] = mapped_column(ForeignKey("progresos.id"))
    titulo: Mapped[str] = mapped_column(String(200))
    tipo: Mapped[str] = mapped_column(String(20))  # tarea | proyecto | examen
    peso: Mapped[float] = mapped_column(Float)  # % dentro del progreso
    horas_estimadas: Mapped[float] = mapped_column(Float)
    fecha_estimada: Mapped[date | None] = mapped_column(Date, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")

    inscripcion: Mapped[Inscripcion] = relationship(back_populates="entregas")
    progreso: Mapped[Progreso] = relationship()
