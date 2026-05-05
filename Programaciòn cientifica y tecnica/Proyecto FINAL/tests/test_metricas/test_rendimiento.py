from observatorio.metricas.rendimiento import (
    calcular_rendimiento_porcentual,
    rendimientos_diarios,
)


def test_rendimiento_positivo():
    assert calcular_rendimiento_porcentual(100, 110) == 10.0


def test_rendimiento_negativo():
    assert calcular_rendimiento_porcentual(100, 90) == -10.0


def test_rendimiento_cero_inicial():
    assert calcular_rendimiento_porcentual(0, 100) == 0.0


def test_rendimiento_iguales():
    assert calcular_rendimiento_porcentual(50, 50) == 0.0


def test_rendimientos_diarios_lista_vacia():
    assert rendimientos_diarios([]) == []


def test_rendimientos_diarios_un_elemento():
    assert rendimientos_diarios([10.0]) == []


def test_rendimientos_diarios_tres():
    assert rendimientos_diarios([100, 110, 99]) == [0.1, -0.1]
