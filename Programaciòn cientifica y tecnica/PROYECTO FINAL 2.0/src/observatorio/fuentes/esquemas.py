"""Modelos Pydantic para validar respuestas de APIs en la frontera.

V2: orden de procesamiento `regex -> Pydantic`. Estos DTOs se aplican sobre datos
ya normalizados por los modulos en `normalizadores/`.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from ..core.tipos import Cotizacion, PuntoPrecio


class CotizacionDTO(BaseModel):
    """DTO validado para una cotizacion actual de un activo."""

    simbolo: str = Field(min_length=1, max_length=20)
    precio: float = Field(gt=0)
    moneda: str = Field(min_length=3, max_length=3)
    timestamp: datetime

    @field_validator("simbolo")
    @classmethod
    def _simbolo_canonico(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("moneda")
    @classmethod
    def _moneda_canonica(cls, v: str) -> str:
        return v.strip().upper()

    def a_dominio(self) -> Cotizacion:
        """Convierte el DTO validado al dataclass del dominio."""
        return Cotizacion(self.simbolo, self.precio, self.moneda, self.timestamp)


class PuntoPrecioDTO(BaseModel):
    """DTO validado para un punto de una serie historica."""

    fecha: datetime
    precio: float = Field(gt=0)

    def a_dominio(self) -> PuntoPrecio:
        return PuntoPrecio(self.fecha, self.precio)


def validar_cotizacion(datos: dict) -> Cotizacion:
    """Valida un dict crudo contra `CotizacionDTO` y devuelve el dataclass del dominio.

    Uso tipico desde una fuente concreta:
        crudo = {"simbolo": "btc ", "precio": 50000, "moneda": "usd", "timestamp": ...}
        cot = validar_cotizacion(crudo)
    """
    return CotizacionDTO.model_validate(datos).a_dominio()


def validar_historico(puntos: list[dict]) -> list[PuntoPrecio]:
    """Valida una lista de puntos contra `PuntoPrecioDTO`."""
    return [PuntoPrecioDTO.model_validate(p).a_dominio() for p in puntos]
