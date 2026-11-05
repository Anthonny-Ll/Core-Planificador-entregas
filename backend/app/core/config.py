"""Configuración leída de variables de entorno (en Render se definen en el panel).

Los valores por defecto solo sirven para trabajar en local. En producción
SECRET_KEY y ADMIN_PASSWORD tienen que venir del entorno.
"""
import os

# Clave con la que se firman los tokens de sesión (JWT).
SECRET_KEY = os.getenv("SECRET_KEY", "solo-para-desarrollo-cambiar-en-produccion")
TOKEN_HORAS = int(os.getenv("TOKEN_HORAS", "8"))

# Administrador global que se crea al arrancar si todavía no existe.
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@udla.edu.ec")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin123*")

# Orígenes permitidos para CORS (React en desarrollo corre en el puerto 5173).
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

# Por defecto, SQLite dentro de backend/. Se puede cambiar con DATABASE_URL.
DATABASE_URL = os.getenv("DATABASE_URL", "")
