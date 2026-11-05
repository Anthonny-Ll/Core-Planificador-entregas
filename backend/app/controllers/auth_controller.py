"""Inicio de sesión y registro de estudiantes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.controllers.errores import rechazar
from app.core.database import get_db
from app.core.security import crear_token, encriptar_password, usuario_actual, verificar_password
from app.models import Usuario
from app.schemas import LoginIn, RegistroIn, TokenOut, UsuarioOut
from app.services.validaciones import validar_registro

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenOut)
def login(datos: LoginIn, db: Session = Depends(get_db)):
    correo = datos.correo.strip().lower()
    usuario = db.scalar(select(Usuario).where(Usuario.correo == correo))
    # Mismo mensaje si no existe o si la clave está mal: no revela qué correos están registrados.
    if usuario is None or not verificar_password(datos.password, usuario.password_hash):
        raise HTTPException(401, "Correo o contraseña incorrectos")
    if not usuario.activo:
        raise HTTPException(403, "Tu cuenta está desactivada. Contacta al administrador.")
    return {"token": crear_token(usuario), "usuario": usuario}


@router.post("/registro", response_model=TokenOut, status_code=201)
def registro(datos: RegistroIn, db: Session = Depends(get_db)):
    """Solo crea estudiantes: el rol admin no se puede pedir desde aquí."""
    correo = datos.correo.strip().lower()
    errores = validar_registro(datos.nombre, correo, datos.password)
    if errores:
        rechazar("No se pudo crear la cuenta.", errores)
    if db.scalar(select(Usuario).where(Usuario.correo == correo)):
        rechazar("No se pudo crear la cuenta.", ["Ya existe una cuenta con ese correo."], 409)
    usuario = Usuario(
        nombre=datos.nombre.strip(), correo=correo,
        password_hash=encriptar_password(datos.password), rol="estudiante",
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return {"token": crear_token(usuario), "usuario": usuario}


@router.get("/yo", response_model=UsuarioOut)
def yo(usuario: Usuario = Depends(usuario_actual)):
    return usuario
