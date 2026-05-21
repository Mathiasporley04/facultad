"""Tests de persistencia: clase AlmacenCifrado, wrappers legacy y CSV/XML."""
from pathlib import Path

import pytest

from observatorio.persistencia.almacen import (
    AlmacenCifrado,
    cargar_portfolio,
    csv_a_tenencias,
    existe_portfolio,
    guardar_portfolio,
    tenencias_a_csv,
    tenencias_a_xml,
    xml_a_tenencias,
)
from observatorio.persistencia.cifrado import ClaveInvalida, cifrar, descifrar


# ---------- cifrado helpers (legacy) ----------


def test_cifrado_roundtrip():
    plano = b"hola mundo"
    token = cifrar(plano, "pass1")
    assert token != plano
    assert descifrar(token, "pass1") == plano


def test_cifrado_password_invalido():
    token = cifrar(b"x", "correcta")
    with pytest.raises(ClaveInvalida):
        descifrar(token, "incorrecta")


# ---------- wrappers legacy ----------


def test_portfolio_roundtrip_legacy(tmp_path: Path):
    archivo = tmp_path / "p.enc"
    tenencias = [
        {"simbolo": "BTC", "tipo": "cripto", "cantidad": 0.5},
        {"simbolo": "AAPL", "tipo": "usa", "cantidad": 10},
    ]
    guardar_portfolio(tenencias, "miPass", path=archivo)
    leidas = cargar_portfolio("miPass", path=archivo)
    assert leidas == tenencias
    assert existe_portfolio(path=archivo)


# ---------- AlmacenCifrado clase ----------


def test_almacen_cifrado_roundtrip(tmp_path: Path):
    almacen = AlmacenCifrado(ruta=tmp_path / "p.enc")
    assert not almacen.existe()
    tenencias = [{"simbolo": "ETH", "tipo": "cripto", "cantidad": 2.0, "precio_compra": 2000.0}]
    almacen.guardar(tenencias, "claveSegura")
    assert almacen.existe()
    leidas = almacen.cargar("claveSegura")
    assert leidas == tenencias


def test_almacen_cifrado_password_invalido(tmp_path: Path):
    almacen = AlmacenCifrado(ruta=tmp_path / "p.enc")
    almacen.guardar([{"simbolo": "BTC", "tipo": "cripto", "cantidad": 1.0}], "buena")
    with pytest.raises(ClaveInvalida):
        almacen.cargar("mala")


def test_almacen_cifrado_no_existe_devuelve_vacio(tmp_path: Path):
    almacen = AlmacenCifrado(ruta=tmp_path / "no-existe.enc")
    assert almacen.cargar("cualquier") == []


# ---------- CSV ----------


def test_csv_roundtrip():
    tenencias = [{"simbolo": "BTC", "tipo": "cripto", "cantidad": 0.25}]
    csv = tenencias_a_csv(tenencias)
    leidas = csv_a_tenencias(csv)
    # V2: el CSV incorpora `precio_compra` canonicamente (default 0.0)
    assert leidas == [
        {"simbolo": "BTC", "tipo": "cripto", "cantidad": 0.25, "precio_compra": 0.0}
    ]


def test_csv_con_precio_compra():
    tenencias = [
        {"simbolo": "BTC", "tipo": "cripto", "cantidad": 0.5, "precio_compra": 30000.0}
    ]
    csv = tenencias_a_csv(tenencias)
    leidas = csv_a_tenencias(csv)
    assert leidas == tenencias


# ---------- XML (directriz 7.1) ----------


def test_xml_roundtrip():
    tenencias = [
        {"simbolo": "BTC", "tipo": "cripto", "cantidad": 0.5, "precio_compra": 30000.0},
        {"simbolo": "AAPL", "tipo": "usa", "cantidad": 10.0, "precio_compra": 150.0},
    ]
    xml = tenencias_a_xml(tenencias)
    assert xml.startswith("<?xml")
    assert "<portfolio>" in xml
    assert 'simbolo="BTC"' in xml
    leidas = xml_a_tenencias(xml)
    assert leidas == tenencias


def test_xml_sin_precio_compra():
    """Tolera tenencias sin precio_compra (default 0.0)."""
    xml = tenencias_a_xml([{"simbolo": "ETH", "tipo": "cripto", "cantidad": 1.5}])
    leidas = xml_a_tenencias(xml)
    assert leidas == [
        {"simbolo": "ETH", "tipo": "cripto", "cantidad": 1.5, "precio_compra": 0.0}
    ]


def test_xml_malformado_devuelve_vacio():
    assert xml_a_tenencias("<<<no-es-xml>>>") == []
