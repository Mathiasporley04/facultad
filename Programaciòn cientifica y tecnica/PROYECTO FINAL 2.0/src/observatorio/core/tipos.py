"""Tipos compartidos del dominio."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TipoMercado(str, Enum):
    CRIPTO = "cripto"
    ACCION_USA = "accion_usa"
    ACCION_ARG = "accion_arg"
    DIVISA = "divisa"


@dataclass(frozen=True)
class PuntoPrecio:
    """Un punto en una serie temporal de precios."""

    fecha: datetime
    precio: float


@dataclass(frozen=True)
class Cotizacion:
    """Cotizacion actual de un activo."""

    simbolo: str
    precio: float
    moneda: str
    timestamp: datetime
