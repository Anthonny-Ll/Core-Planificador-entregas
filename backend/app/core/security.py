"""Seguridad: hash de contraseñas, tokens JWT y protección de rutas por rol."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import SECRET_KEY, TOKEN_HORAS
from app.core.database import get_db
from app.models import Usuario

ITERACIONES = 200_000  # PBKDF2-SHA256: lento a propósito para que adivinar sea caro.


def encriptar_password(password: str) -> str:
    """Devuelve 'sal$hash'. La contraseña nunca se guarda en texto plano."""
    sal = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(sal), ITERACIONES)
    return f"{sal}${digest.hex()}"


def verificar_password(password: str, guardado: str) -> bool:
    """Recalcula el hash con la misma sal y lo compara en tiempo constante."""
    try:
        sal, esperado = guardado.split("$", 1)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(sal), ITERACIONES)
    return hmac.compare_digest(digest.hex(), esperado)


def crear_token(usuario: Usuario) -> str:
    """Token firmado con el id y el rol del usuario; vence en TOKEN_HORAS."""
    datos = {
        "sub": str(usuario.id),
        "rol": usuario.rol,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_HORAS),
    }
    return jwt.encode(datos, SECRET_KEY, algorithm="HS256")


bearer = HTTPBearer(auto_error=False)


def usuario_actual(
    cred: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    """Dependencia: lee el token del header Authorization y devuelve el usuario."""
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Inicia sesión para continuar")
    try:
        datos = jwt.decode(cred.credentials, SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sesión inválida o vencida")
    usuario = db.get(Usuario, int(datos["sub"]))
    if usuario is None or not usuario.activo:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario inexistente o desactivado")
    return usuario


def solo_admin(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
    """Dependencia: deja pasar únicamente a usuarios con rol admin (si no, 403)."""
    if usuario.rol != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo el administrador puede hacer esto")
    return usuario


def solo_estudiante(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
    if usuario.rol != "estudiante":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Esta sección es para estudiantes")
    return usuario
