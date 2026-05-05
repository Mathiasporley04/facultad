from datetime import datetime, timezone

from observatorio.normalizadores import es_ticker_valido, normalizar_ticker, parsear_fecha


def test_normalizar_ticker_basico():
    assert normalizar_ticker("BTC") == "BTC"


def test_normalizar_ticker_quita_sufijo_usd():
    assert normalizar_ticker("BTC-USD") == "BTC"
    assert normalizar_ticker("btcusdt") == "BTC"
    assert normalizar_ticker("ETH/USDC") == "ETH"


def test_normalizar_ticker_indice_preserva_prefijo():
    assert normalizar_ticker("^GSPC") == "^GSPC"


def test_normalizar_ticker_vacio():
    assert normalizar_ticker("") == ""
    assert normalizar_ticker("   ") == ""


def test_normalizar_ticker_limpia_espacios_y_caracteres():
    assert normalizar_ticker(" aapl! ") == "AAPL"


def test_es_ticker_valido():
    assert es_ticker_valido("AAPL")
    assert es_ticker_valido("^GSPC")
    assert es_ticker_valido("BRK.B")
    assert not es_ticker_valido("")
    assert not es_ticker_valido("muylargoticker")
    assert not es_ticker_valido("AB CD")


def test_parsear_fecha_iso():
    dt = parsear_fecha("2025-01-15T12:30:00")
    assert dt.year == 2025 and dt.month == 1 and dt.day == 15
    assert dt.tzinfo is not None


def test_parsear_fecha_unix_segundos():
    dt = parsear_fecha("1700000000")
    assert dt.year == 2023


def test_parsear_fecha_unix_ms():
    dt = parsear_fecha("1700000000000")
    assert dt.year == 2023


def test_parsear_fecha_datetime_naive():
    dt = parsear_fecha(datetime(2024, 5, 1))
    assert dt.tzinfo == timezone.utc
