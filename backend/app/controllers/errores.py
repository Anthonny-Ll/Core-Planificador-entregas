"""Respuestas de error con el mismo formato en toda la API."""
from fastapi import HTTPException


def rechazar(mensaje: str, errores: list[str], codigo: int = 422):
    """Corta la petición ANTES de grabar y explica qué falló.

    Respuesta: {"detail": {"mensaje": "...", "errores": ["...", "..."]}}
    """
    raise HTTPException(status_code=codigo, detail={"mensaje": mensaje, "errores": errores})
