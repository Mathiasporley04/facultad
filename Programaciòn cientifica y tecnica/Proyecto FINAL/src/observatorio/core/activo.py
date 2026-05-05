"""ABC Activo: jerarquia polimorfica de activos financieros."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from .fuente import FuenteDatos
from .tipos import PuntoPrecio, TipoMercado


class Activo(ABC):
    """Activo financiero abstracto."""

    def __init__(
        self,
        simbolo: str,
        nombre: str,
        moneda_nativa: str,
        fuente: FuenteDatos,
    ) -> None:
        self.simbolo = simbolo
        self.nombre = nombre
        self.moneda_nativa = moneda_nativa
        self.fuente = fuente

    @property
    @abstractmethod
    def tipo(self) -> TipoMercado: ...

    @abstractmethod
    def precio_actual_usd(self, tasas: dict[str, float] | None = None) -> float:
        """Precio actual en USD. Algunas subclases requieren `tasas`."""

    def obtener_historico(self, desde: datetime, hasta: datetime) -> list[PuntoPrecio]:
        """Delega en la fuente. Es un metodo de instancia comun a todos."""
        return self.fuente.historico(self.simbolo, desde, hasta)

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.simbolo}>"
