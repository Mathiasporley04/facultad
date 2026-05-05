"""Excepciones del dominio."""


class ObservatorioError(Exception):
    """Base de toda excepcion del proyecto."""


class FuenteIndisponible(ObservatorioError):
    """Una fuente de datos externa fallo o no respondio."""


class ActivoNoEncontrado(ObservatorioError):
    """El simbolo solicitado no existe en la fuente."""


class DatoInvalido(ObservatorioError):
    """Un dato recibido no paso validacion."""
