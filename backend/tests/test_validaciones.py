"""Pruebas de las reglas de negocio (funciones puras, sin BD)."""
from datetime import date

from app.services.validaciones import (
    normalizar_codigo, validar_asignatura, validar_entrega, validar_periodo, validar_pesos_progresos,
)


def test_pesos_que_suman_100_son_validos():
    assert validar_pesos_progresos([30, 30, 40]) == []
    assert validar_pesos_progresos([33.33, 33.33, 33.34]) == []


def test_pesos_que_no_suman_100():
    errores = validar_pesos_progresos([30, 40, 40])
    assert errores == ["Los pesos de los progresos deben sumar 100. Suma actual: 110."]


def test_peso_negativo_o_cero():
    errores = validar_pesos_progresos([-10, 50, 60])
    assert any("Progreso 1" in e for e in errores)
    assert validar_pesos_progresos([0, 50, 50])  # 0 no se permite


def test_cantidad_de_progresos():
    assert validar_pesos_progresos([50, 50]) == ["Debe haber exactamente 3 progresos (se recibieron 2)."]


def test_codigo_de_asignatura():
    assert normalizar_codigo(" iswz3101 ") == "ISWZ3101"
    assert validar_asignatura("ISWZ3101", "Ingeniería Web", 3, 10, [30, 30, 40]) == []
    assert validar_asignatura("ISW3101", "Ingeniería Web", 3, 10, [30, 30, 40])


def test_creditos_y_escala():
    errores = validar_asignatura("ISWZ3101", "Ingeniería Web", 0, 0, [30, 30, 40])
    assert len(errores) == 2


def test_entrega_que_pasa_del_100_del_progreso():
    errores = validar_entrega("Documento", "proyecto", 50, 4, peso_ya_cargado=60)
    assert errores and "Queda disponible 40 %" in errores[0]
    assert validar_entrega("Documento", "proyecto", 40, 4, peso_ya_cargado=60) == []


def test_periodo():
    assert validar_periodo("2026-2", date(2026, 9, 1), date(2027, 1, 31)) == []
    assert len(validar_periodo("2026-B", date(2026, 9, 1), date(2026, 8, 1))) == 2
