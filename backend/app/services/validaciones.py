"""Reglas de negocio que se validan en el BACKEND antes de grabar en la base de datos.

Son funciones puras: reciben datos y devuelven la lista de errores encontrados
(vacía si todo está bien). No dependen de FastAPI ni de la BD, así que se
prueban directamente con pytest (tests/test_validaciones.py).

El dato sensible del core son los PESOS DE LOS PROGRESOS de una asignatura:
con ellos se calcula la nota final, la nota necesaria para llegar a la meta y la
prioridad de cada entrega en el plan de estudio. Si se grabaran pesos que no
suman 100, todos los cálculos de todos los estudiantes inscritos saldrían mal.
Por eso no basta con validarlos en JavaScript: cualquiera puede saltarse el
formulario y llamar a la API directamente (curl, Postman, /docs).
"""
import re
from datetime import date

PATRON_CODIGO_ASIGNATURA = re.compile(r"^[A-Z]{4}\d{4}$")  # ej. ISWZ3101
PATRON_CODIGO_CARRERA = re.compile(r"^[A-Z]{2,10}$")  # ej. ISW
PATRON_PERIODO = re.compile(r"^\d{4}-[12]$")  # ej. 2026-2
PATRON_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
PATRON_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")

TIPOS_ENTREGA = {"tarea", "proyecto", "examen"}
TOLERANCIA = 0.01  # para comparar decimales (33.33 + 33.33 + 33.34)


def normalizar_codigo(codigo: str) -> str:
    """'  iswz3101 ' -> 'ISWZ3101'."""
    return (codigo or "").strip().upper()


def validar_pesos_progresos(pesos: list[float]) -> list[str]:
    """Los 3 progresos: cada peso entre 0 y 100 (sin incluir 0) y la suma exactamente 100."""
    errores = []
    if len(pesos) != 3:
        return [f"Debe haber exactamente 3 progresos (se recibieron {len(pesos)})."]
    for numero, peso in enumerate(pesos, start=1):
        if not 0 < peso <= 100:
            errores.append(f"El peso del Progreso {numero} debe ser mayor que 0 y como máximo 100.")
    suma = round(sum(pesos), 2)
    if abs(suma - 100) > TOLERANCIA:
        errores.append(f"Los pesos de los progresos deben sumar 100. Suma actual: {suma:g}.")
    return errores


def validar_asignatura(codigo: str, nombre: str, creditos: int, escala: float, pesos: list[float]) -> list[str]:
    """Todo lo que debe cumplir una asignatura antes de grabarse."""
    errores = []
    if not PATRON_CODIGO_ASIGNATURA.match(codigo):
        errores.append("El código debe tener 4 letras y 4 dígitos (ej. ISWZ3101).")
    if not 3 <= len((nombre or "").strip()) <= 100:
        errores.append("El nombre debe tener entre 3 y 100 caracteres.")
    if not 1 <= creditos <= 10:
        errores.append("Los créditos deben ser un entero entre 1 y 10.")
    if not 0 < escala <= 100:
        errores.append("La escala de calificación debe ser mayor que 0 y como máximo 100.")
    errores += validar_pesos_progresos(pesos)
    return errores


def validar_carrera(codigo: str, nombre: str) -> list[str]:
    errores = []
    if not PATRON_CODIGO_CARRERA.match(codigo):
        errores.append("El código de la carrera debe tener entre 2 y 10 letras (ej. ISW).")
    if not 3 <= len((nombre or "").strip()) <= 100:
        errores.append("El nombre debe tener entre 3 y 100 caracteres.")
    return errores


def validar_periodo(nombre: str, inicio: date, fin: date) -> list[str]:
    errores = []
    if not PATRON_PERIODO.match((nombre or "").strip()):
        errores.append("El nombre del período debe tener el formato AAAA-1 o AAAA-2 (ej. 2026-2).")
    if fin <= inicio:
        errores.append("La fecha de fin debe ser posterior a la fecha de inicio.")
    return errores


def validar_registro(nombre: str, correo: str, password: str) -> list[str]:
    errores = []
    if not 3 <= len((nombre or "").strip()) <= 100:
        errores.append("El nombre debe tener entre 3 y 100 caracteres.")
    if not PATRON_CORREO.match((correo or "").strip()):
        errores.append("El correo no tiene un formato válido.")
    if len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        errores.append("La contraseña debe tener al menos 8 caracteres, con letras y números.")
    return errores


def validar_inscripcion(nota_meta: float | None, escala: float, color: str) -> list[str]:
    errores = []
    if nota_meta is not None and not 0 <= nota_meta <= escala:
        errores.append(f"La nota meta debe estar entre 0 y {escala:g}.")
    if not PATRON_COLOR.match(color or ""):
        errores.append("El color debe tener el formato #RRGGBB.")
    return errores


def validar_entrega(titulo: str, tipo: str, peso: float, horas: float, peso_ya_cargado: float) -> list[str]:
    """peso_ya_cargado: suma de los pesos de las otras entregas del mismo progreso."""
    errores = []
    if not 3 <= len((titulo or "").strip()) <= 200:
        errores.append("El título debe tener entre 3 y 200 caracteres.")
    if tipo not in TIPOS_ENTREGA:
        errores.append("El tipo debe ser tarea, proyecto o examen.")
    if not 0 < peso <= 100:
        errores.append("El peso en el progreso debe ser mayor que 0 y como máximo 100.")
    elif peso_ya_cargado + peso > 100 + TOLERANCIA:
        disponible = round(100 - peso_ya_cargado, 2)
        errores.append(
            f"Con esta entrega el progreso pasaría de 100 % ({peso_ya_cargado + peso:g}/100). "
            f"Queda disponible {disponible:g} %."
        )
    if not 0 < horas <= 200:
        errores.append("Las horas estimadas deben ser mayores que 0 y como máximo 200.")
    return errores
