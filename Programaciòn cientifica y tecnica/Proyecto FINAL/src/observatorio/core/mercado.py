"""Clase Mercado: agrega activos del mismo origen."""
from __future__ import annotations

from .activo import Activo
from .tipos import TipoMercado


class Mercado:
    """Coleccion de activos del mismo tipo de mercado."""

    def __init__(self, nombre: str, tipo: TipoMercado, activos: list[Activo] | None = None) -> None:
        self.nombre = nombre
        self.tipo = tipo
        self.activos: list[Activo] = activos or []

    def agregar(self, activo: Activo) -> None:
        self.activos.append(activo)

    def simbolos(self) -> list[str]:
        return [a.simbolo for a in self.activos]

    def __len__(self) -> int:
        return len(self.activos)
