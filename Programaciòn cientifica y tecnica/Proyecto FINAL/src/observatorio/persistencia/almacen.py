"""Persistencia del portfolio cifrado en disco."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from .cifrado import cifrar, descifrar

_DEFAULT_PATH = Path("data/portfolio/portfolio.enc")


def guardar_portfolio(tenencias: list[dict], password: str, path: Path = _DEFAULT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plano = json.dumps(tenencias, ensure_ascii=False).encode("utf-8")
    path.write_bytes(cifrar(plano, password))


def cargar_portfolio(password: str, path: Path = _DEFAULT_PATH) -> list[dict]:
    if not path.exists():
        return []
    plano = descifrar(path.read_bytes(), password)
    return json.loads(plano.decode("utf-8"))


def existe_portfolio(path: Path = _DEFAULT_PATH) -> bool:
    return path.exists()


def tenencias_a_csv(tenencias: list[dict]) -> str:
    if not tenencias:
        return "simbolo,tipo,cantidad\n"
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["simbolo", "tipo", "cantidad"])
    writer.writeheader()
    for t in tenencias:
        writer.writerow({"simbolo": t["simbolo"], "tipo": t["tipo"], "cantidad": t["cantidad"]})
    return buf.getvalue()


def csv_a_tenencias(texto: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(texto))
    salida = []
    for fila in reader:
        try:
            salida.append(
                {
                    "simbolo": fila["simbolo"].strip().upper(),
                    "tipo": fila["tipo"].strip().lower(),
                    "cantidad": float(fila["cantidad"]),
                }
            )
        except (KeyError, ValueError):
            continue
    return salida
