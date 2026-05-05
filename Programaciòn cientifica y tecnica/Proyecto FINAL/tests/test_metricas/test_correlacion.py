from observatorio.metricas.correlacion import calcular_correlacion, matriz_correlacion


def test_correlacion_perfecta_positiva():
    a = [1, 2, 3, 4, 5]
    b = [2, 4, 6, 8, 10]
    assert abs(calcular_correlacion(a, b) - 1.0) < 1e-9


def test_correlacion_perfecta_negativa():
    a = [1, 2, 3, 4, 5]
    b = [5, 4, 3, 2, 1]
    assert abs(calcular_correlacion(a, b) - (-1.0)) < 1e-9


def test_correlacion_lista_corta():
    assert calcular_correlacion([1.0], [1.0]) == 0.0


def test_correlacion_constante():
    # Si una serie es constante la varianza es cero -> 0.0
    assert calcular_correlacion([1, 1, 1], [1, 2, 3]) == 0.0


def test_matriz_correlacion_diagonal_es_uno():
    series = {"A": [1, 2, 3, 4], "B": [2, 4, 6, 8]}
    m = matriz_correlacion(series)
    assert abs(m["A"]["A"] - 1.0) < 1e-9
    assert abs(m["A"]["B"] - 1.0) < 1e-9
