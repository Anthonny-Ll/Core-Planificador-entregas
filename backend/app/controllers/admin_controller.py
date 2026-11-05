"""Rutas del ADMINISTRADOR: carreras, asignaturas, períodos y usuarios.

Todas exigen un token con rol admin (dependencia solo_admin → 403 si no lo es).
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.controllers.errores import rechazar
from app.core.database import get_db
from app.core.security import solo_admin
from app.models import Asignatura, Carrera, Inscripcion, Periodo, Progreso, Usuario
from app.schemas import (
    AsignaturaIn, AsignaturaOut, CarreraIn, CarreraOut, EstadoUsuarioIn,
    PeriodoIn, PeriodoOut, UsuarioOut,
)
from app.services.validaciones import (
    normalizar_codigo, validar_asignatura, validar_carrera, validar_periodo,
)

router = APIRouter(prefix="/api/admin", tags=["Administración"], dependencies=[Depends(solo_admin)])


def buscar(db: Session, modelo, id_: int, nombre: str):
    obj = db.get(modelo, id_)
    if obj is None:
        raise HTTPException(404, f"{nombre} no encontrada")
    return obj


# ---------------------------------------------------------------- Carreras
@router.get("/carreras", response_model=list[CarreraOut])
def listar_carreras(db: Session = Depends(get_db)):
    return db.scalars(select(Carrera).order_by(Carrera.nombre)).all()


def _guardar_carrera(db: Session, datos: CarreraIn, carrera: Carrera | None) -> Carrera:
    codigo = normalizar_codigo(datos.codigo)
    errores = validar_carrera(codigo, datos.nombre)
    if errores:
        rechazar("No se guardó la carrera.", errores)
    repetida = db.scalar(select(Carrera).where(Carrera.codigo == codigo))
    if repetida and (carrera is None or repetida.id != carrera.id):
        rechazar("No se guardó la carrera.", [f"Ya existe una carrera con el código {codigo}."], 409)
    carrera = carrera or Carrera()
    carrera.codigo, carrera.nombre = codigo, datos.nombre.strip()
    db.add(carrera)
    db.commit()
    db.refresh(carrera)
    return carrera


@router.post("/carreras", response_model=CarreraOut, status_code=201)
def crear_carrera(datos: CarreraIn, db: Session = Depends(get_db)):
    return _guardar_carrera(db, datos, None)


@router.put("/carreras/{carrera_id}", response_model=CarreraOut)
def editar_carrera(carrera_id: int, datos: CarreraIn, db: Session = Depends(get_db)):
    return _guardar_carrera(db, datos, buscar(db, Carrera, carrera_id, "Carrera"))


@router.delete("/carreras/{carrera_id}", status_code=204)
def borrar_carrera(carrera_id: int, db: Session = Depends(get_db)):
    carrera = buscar(db, Carrera, carrera_id, "Carrera")
    if carrera.asignaturas:
        rechazar("No se puede borrar la carrera.",
                 [f"Tiene {len(carrera.asignaturas)} asignatura(s). Bórralas o muévelas primero."], 409)
    db.delete(carrera)
    db.commit()
    return Response(status_code=204)


# ------------------------------------------------------------- Asignaturas
@router.get("/asignaturas", response_model=list[AsignaturaOut])
def listar_asignaturas(carrera_id: int | None = None, db: Session = Depends(get_db)):
    consulta = select(Asignatura).order_by(Asignatura.codigo)
    if carrera_id:
        consulta = consulta.where(Asignatura.carrera_id == carrera_id)
    return db.scalars(consulta).all()


def _guardar_asignatura(db: Session, datos: AsignaturaIn, asignatura: Asignatura | None) -> Asignatura:
    """VALIDACIÓN EN BACKEND del dato sensible (pesos de progresos) antes de grabar."""
    codigo = normalizar_codigo(datos.codigo)
    mensaje = "No se guardó la asignatura."

    # 1) Reglas de negocio: formato del código, créditos, escala y pesos que sumen 100.
    errores = validar_asignatura(codigo, datos.nombre, datos.creditos, datos.escala, datos.pesos)
    # 2) La carrera elegida en el dropdown tiene que existir de verdad.
    if db.get(Carrera, datos.carrera_id) is None:
        errores.append("La carrera elegida no existe.")
    if errores:
        rechazar(mensaje, errores)  # 422: no se toca la base de datos
    # 3) Código único.
    repetida = db.scalar(select(Asignatura).where(Asignatura.codigo == codigo))
    if repetida and (asignatura is None or repetida.id != asignatura.id):
        rechazar(mensaje, [f"Ya existe una asignatura con el código {codigo}."], 409)

    # Recién aquí se graba.
    asignatura = asignatura or Asignatura()
    asignatura.carrera_id = datos.carrera_id
    asignatura.codigo = codigo
    asignatura.nombre = datos.nombre.strip()
    asignatura.creditos = datos.creditos
    asignatura.escala = datos.escala
    if asignatura.progresos:  # al editar se actualizan los pesos, los ids se mantienen
        for progreso, peso in zip(asignatura.progresos, datos.pesos):
            progreso.peso = round(peso, 2)
    else:
        asignatura.progresos = [Progreso(numero=n, peso=round(p, 2)) for n, p in enumerate(datos.pesos, 1)]
    db.add(asignatura)
    db.commit()
    db.refresh(asignatura)
    return asignatura


@router.post("/asignaturas", response_model=AsignaturaOut, status_code=201)
def crear_asignatura(datos: AsignaturaIn, db: Session = Depends(get_db)):
    return _guardar_asignatura(db, datos, None)


@router.put("/asignaturas/{asignatura_id}", response_model=AsignaturaOut)
def editar_asignatura(asignatura_id: int, datos: AsignaturaIn, db: Session = Depends(get_db)):
    return _guardar_asignatura(db, datos, buscar(db, Asignatura, asignatura_id, "Asignatura"))


@router.delete("/asignaturas/{asignatura_id}", status_code=204)
def borrar_asignatura(asignatura_id: int, db: Session = Depends(get_db)):
    asignatura = buscar(db, Asignatura, asignatura_id, "Asignatura")
    inscritos = db.scalar(select(func.count()).where(Inscripcion.asignatura_id == asignatura_id))
    if inscritos:
        rechazar("No se puede borrar la asignatura.", [f"Tiene {inscritos} estudiante(s) inscrito(s)."], 409)
    db.delete(asignatura)
    db.commit()
    return Response(status_code=204)


# ---------------------------------------------------------------- Períodos
@router.get("/periodos", response_model=list[PeriodoOut])
def listar_periodos(db: Session = Depends(get_db)):
    return db.scalars(select(Periodo).order_by(Periodo.fecha_inicio.desc())).all()


def _guardar_periodo(db: Session, datos: PeriodoIn, periodo: Periodo | None) -> Periodo:
    nombre = datos.nombre.strip()
    errores = validar_periodo(nombre, datos.fecha_inicio, datos.fecha_fin)
    if errores:
        rechazar("No se guardó el período.", errores)
    repetido = db.scalar(select(Periodo).where(Periodo.nombre == nombre))
    if repetido and (periodo is None or repetido.id != periodo.id):
        rechazar("No se guardó el período.", [f"Ya existe el período {nombre}."], 409)
    if datos.activo:  # solo un período activo a la vez
        db.execute(update(Periodo).values(activo=False))
    periodo = periodo or Periodo()
    periodo.nombre, periodo.fecha_inicio, periodo.fecha_fin = nombre, datos.fecha_inicio, datos.fecha_fin
    periodo.activo = datos.activo
    db.add(periodo)
    db.commit()
    db.refresh(periodo)
    return periodo


@router.post("/periodos", response_model=PeriodoOut, status_code=201)
def crear_periodo(datos: PeriodoIn, db: Session = Depends(get_db)):
    return _guardar_periodo(db, datos, None)


@router.put("/periodos/{periodo_id}", response_model=PeriodoOut)
def editar_periodo(periodo_id: int, datos: PeriodoIn, db: Session = Depends(get_db)):
    return _guardar_periodo(db, datos, buscar(db, Periodo, periodo_id, "Período"))


@router.delete("/periodos/{periodo_id}", status_code=204)
def borrar_periodo(periodo_id: int, db: Session = Depends(get_db)):
    periodo = buscar(db, Periodo, periodo_id, "Período")
    if db.scalar(select(func.count()).where(Inscripcion.periodo_id == periodo_id)):
        rechazar("No se puede borrar el período.", ["Tiene inscripciones de estudiantes."], 409)
    db.delete(periodo)
    db.commit()
    return Response(status_code=204)


# ---------------------------------------------------------------- Usuarios
@router.get("/usuarios", response_model=list[UsuarioOut])
def listar_usuarios(db: Session = Depends(get_db)):
    return db.scalars(select(Usuario).order_by(Usuario.rol, Usuario.nombre)).all()


@router.patch("/usuarios/{usuario_id}", response_model=UsuarioOut)
def cambiar_estado_usuario(
    usuario_id: int, datos: EstadoUsuarioIn,
    db: Session = Depends(get_db), admin: Usuario = Depends(solo_admin),
):
    usuario = buscar(db, Usuario, usuario_id, "Usuario")
    if usuario.id == admin.id and not datos.activo:
        rechazar("No se cambió el estado.", ["No puedes desactivar tu propia cuenta."], 409)
    usuario.activo = datos.activo
    db.commit()
    db.refresh(usuario)
    return usuario
