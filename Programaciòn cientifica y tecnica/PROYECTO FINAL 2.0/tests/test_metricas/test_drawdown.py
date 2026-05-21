from observatorio.metricas.drawdown import calcular_drawdown_maximo


def test_drawdown_lista_vacia():
    assert calcular_drawdown_maximo([]) == 0.0


def test_drawdown_serie_creciente():
    assert calcular_drawdown_maximo([1, 2, 3, 4, 5]) == 0.0


def test_drawdown_caida_50_pct():
    # 100 -> 50 = -50%
    assert abs(calcular_drawdown_maximo([100, 50]) - (-0.5)) < 1e-9


def test_drawdown_solo_peor_caida():
    # 100 -> 80 (-20%), recupera a 120, baja a 60 (-50%)
    assert abs(calcular_drawdown_maximo([100, 80, 120, 60]) - (-0.5)) < 1e-9


def test_drawdown_unico_elemento():
    assert calcular_drawdown_maximo([100]) == 0.0
