import pytest

from observatorio.persistencia.almacen import (
    cargar_portfolio,
    csv_a_tenencias,
    guardar_portfolio,
    tenencias_a_csv,
)
from observatorio.persistencia.cifrado import ClaveInvalida, cifrar, descifrar


def test_cifrado_roundtrip():
    plano = b"hola mundo"
    token = cifrar(plano, "pass1")
    assert token != plano
    assert descifrar(token, "pass1") == plano


def test_cifrado_password_invalido():
    token = cifrar(b"x", "correcta")
    with pytest.raises(ClaveInvalida):
        descifrar(token, "incorrecta")


def test_portfolio_roundtrip(tmp_path):
    archivo = tmp_path / "p.enc"
    tenencias = [
        {"simbolo": "BTC", "tipo": "cripto", "cantidad": 0.5},
        {"simbolo": "AAPL", "tipo": "usa", "cantidad": 10},
    ]
    guardar_portfolio(tenencias, "miPass", path=archivo)
    leidas = cargar_portfolio("miPass", path=archivo)
    assert leidas == tenencias


def test_csv_roundtrip():
    tenencias = [{"simbolo": "BTC", "tipo": "cripto", "cantidad": 0.25}]
    csv = tenencias_a_csv(tenencias)
    leidas = csv_a_tenencias(csv)
    assert leidas == tenencias
