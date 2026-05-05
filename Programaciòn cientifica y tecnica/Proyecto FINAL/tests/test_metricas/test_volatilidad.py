from observatorio.metricas.volatilidad import calcular_volatilidad, clasificar_volatilidad


def test_volatilidad_lista_vacia():
    assert calcular_volatilidad([]) == 0.0


def test_volatilidad_constante_es_cero():
    assert calcular_volatilidad([100, 100, 100, 100]) == 0.0


def test_volatilidad_positiva():
    precios = [100, 110, 105, 115, 100, 120]
    assert calcular_volatilidad(precios) > 0


def test_clasificar_estable():
    assert clasificar_volatilidad(0.1) == "Estable"


def test_clasificar_moderada():
    assert clasificar_volatilidad(0.2) == "Moderada"


def test_clasificar_alta():
    assert clasificar_volatilidad(0.45) == "Alta"


def test_clasificar_muy_alta():
    assert clasificar_volatilidad(1.0) == "Muy alta"
