"""Rutas del ESTUDIANTE y fuentes de los dropdowns en cascada.

Cascada 1 (Inscribir materia):  Período  +  Carrera  →  Asignaturas de esa carrera
Cascada 2 (Nueva entrega):       Materia inscrita     →  Progresos de esa asignatura
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.controllers.errores import rechazar
from app.core.database import get_db
from app.core.security import solo_estudiante, usuario_actual
from app.models import Asignatura, Carrera, Entrega, Inscripcion, Periodo, Progreso, Usuario
from app.schemas import (
    AsignaturaOut, CarreraOut, EntregaIn, EntregaOut, InscripcionIn, InscripcionOut,
    PeriodoOut, ProgresoCargaOut,
)
from app.services.validaciones import validar_entrega, validar_inscripcion

router = APIRouter(prefix="/api", tags=["Estudiante"])


# ------------------------------------------------- Catálogo para dropdowns
@router.get("/catalogo/periodos", response_model=list[PeriodoOut], dependencies=[Depends(usuario_actual)])
def periodos(db: Session = Depends(get_db)):
    return db.scalars(select(Periodo).order_by(Periodo.activo.desc(), Periodo.fecha_inicio.desc())).all()


@router.get("/catalogo/carreras", response_model=list[CarreraOut], dependencies=[Depends(usuario_actual)])
def carreras(db: Session = Depends(get_db)):
    return db.scalars(select(Carrera).order_by(Carrera.nombre)).all()


@router.get(
    "/catalogo/carreras/{carrera_id}/asignaturas",
    response_model=list[AsignaturaOut], dependencies=[Depends(usuario_actual)],
)
def asignaturas_de_carrera(carrera_id: int, db: Session = Depends(get_db)):
    """Se llama cada vez que el estudiante cambia la carrera en el formulario."""
    if db.get(Carrera, carrera_id) is None:
        raise HTTPException(404, "Carrera no encontrada")
    return db.scalars(
        select(Asignatura).where(Asignatura.carrera_id == carrera_id).order_by(Asignatura.codigo)
    ).all()


# ------------------------------------------------------------ Inscripciones
def mi_inscripcion(db: Session, inscripcion_id: int, usuario: Usuario) -> Inscripcion:
    """Una inscripción de OTRO estudiante se trata como inexistente (404)."""
    insc = db.get(Inscripcion, inscripcion_id)
    if insc is None or insc.usuario_id != usuario.id:
        raise HTTPException(404, "Materia no encontrada")
    return insc


@router.get("/inscripciones", response_model=list[InscripcionOut])
def mis_inscripciones(db: Session = Depends(get_db), usuario: Usuario = Depends(solo_estudiante)):
    return db.scalars(
        select(Inscripcion).where(Inscripcion.usuario_id == usuario.id).order_by(Inscripcion.id)
    ).all()


@router.post("/inscripciones", response_model=InscripcionOut, status_code=201)
def inscribir(datos: InscripcionIn, db: Session = Depends(get_db), usuario: Usuario = Depends(solo_estudiante)):
    mensaje = "No se inscribió la materia."
    periodo = db.get(Periodo, datos.periodo_id)
    asignatura = db.get(Asignatura, datos.asignatura_id)
    errores = []
    if periodo is None:
        errores.append("El período elegido no existe.")
    if asignatura is None:
        errores.append("La asignatura elegida no existe.")
    if errores:
        rechazar(mensaje, errores)
    errores = validar_inscripcion(datos.nota_meta, asignatura.escala, datos.color)
    if errores:
        rechazar(mensaje, errores)
    ya = db.scalar(select(Inscripcion).where(
        Inscripcion.usuario_id == usuario.id,
        Inscripcion.asignatura_id == asignatura.id,
        Inscripcion.periodo_id == periodo.id,
    ))
    if ya:
        rechazar(mensaje, [f"Ya tienes {asignatura.nombre} inscrita en {periodo.nombre}."], 409)
    insc = Inscripcion(
        usuario_id=usuario.id, asignatura_id=asignatura.id, periodo_id=periodo.id,
        nota_meta=datos.nota_meta, color=datos.color,
    )
    db.add(insc)
    db.commit()
    db.refresh(insc)
    return insc


@router.delete("/inscripciones/{inscripcion_id}", status_code=204)
def borrar_inscripcion(inscripcion_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(solo_estudiante)):
    db.delete(mi_inscripcion(db, inscripcion_id, usuario))
    db.commit()
    return Response(status_code=204)


def peso_cargado(db: Session, inscripcion_id: int, progreso_id: int, excluir_id: int | None = None) -> float:
    consulta = select(func.coalesce(func.sum(Entrega.peso), 0)).where(
        Entrega.inscripcion_id == inscripcion_id, Entrega.progreso_id == progreso_id
    )
    if excluir_id:
        consulta = consulta.where(Entrega.id != excluir_id)
    return float(db.scalar(consulta))


@router.get("/inscripciones/{inscripcion_id}/progresos", response_model=list[ProgresoCargaOut])
def progresos_de_materia(inscripcion_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(solo_estudiante)):
    """Se llama cada vez que el estudiante cambia la materia en 'Nueva entrega'."""
    insc = mi_inscripcion(db, inscripcion_id, usuario)
    return [
        {"id": p.id, "numero": p.numero, "peso": p.peso, "cargado": peso_cargado(db, insc.id, p.id)}
        for p in insc.asignatura.progresos
    ]


# ----------------------------------------------------------------- Entregas
def a_salida(e: Entrega) -> dict:
    return {
        **{c: getattr(e, c) for c in (
            "id", "inscripcion_id", "progreso_id", "titulo", "tipo", "peso",
            "horas_estimadas", "fecha_estimada", "estado",
        )},
        "progreso": e.progreso,
        "peso_final": round(e.peso * e.progreso.peso / 100, 2),
    }


@router.get("/entregas", response_model=list[EntregaOut])
def mis_entregas(inscripcion_id: int | None = None, db: Session = Depends(get_db), usuario: Usuario = Depends(solo_estudiante)):
    consulta = (
        select(Entrega).join(Inscripcion).join(Progreso)
        .where(Inscripcion.usuario_id == usuario.id)
        .order_by(Entrega.inscripcion_id, Progreso.numero, Entrega.id)
    )
    if inscripcion_id:
        consulta = consulta.where(Entrega.inscripcion_id == inscripcion_id)
    return [a_salida(e) for e in db.scalars(consulta).all()]


@router.post("/entregas", response_model=EntregaOut, status_code=201)
def crear_entrega(datos: EntregaIn, db: Session = Depends(get_db), usuario: Usuario = Depends(solo_estudiante)):
    mensaje = "No se guardó la entrega."
    insc = mi_inscripcion(db, datos.inscripcion_id, usuario)
    progreso = db.get(Progreso, datos.progreso_id)
    # El progreso tiene que ser de la MISMA asignatura de la materia elegida.
    if progreso is None or progreso.asignatura_id != insc.asignatura_id:
        rechazar(mensaje, ["El progreso elegido no pertenece a esa materia."])
    errores = validar_entrega(
        datos.titulo, datos.tipo, datos.peso, datos.horas_estimadas,
        peso_cargado(db, insc.id, progreso.id),
    )
    if errores:
        rechazar(mensaje, errores)
    entrega = Entrega(
        inscripcion_id=insc.id, progreso_id=progreso.id, titulo=datos.titulo.strip(),
        tipo=datos.tipo, peso=round(datos.peso, 2), horas_estimadas=datos.horas_estimadas,
        fecha_estimada=datos.fecha_estimada,
    )
    db.add(entrega)
    db.commit()
    db.refresh(entrega)
    return a_salida(entrega)


@router.delete("/entregas/{entrega_id}", status_code=204)
def borrar_entrega(entrega_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(solo_estudiante)):
    entrega = db.get(Entrega, entrega_id)
    if entrega is None or entrega.inscripcion.usuario_id != usuario.id:
        raise HTTPException(404, "Entrega no encontrada")
    db.delete(entrega)
    db.commit()
    return Response(status_code=204)
