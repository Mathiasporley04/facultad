"""Wrapper sobre Fernet con derivacion de clave por password (PBKDF2)."""
from __future__ import annotations

import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..core.excepciones import ObservatorioError

_SALT = b"observatorio-latam-v1"  # salt fijo: portfolio personal local, no multi-usuario
_ITER = 200_000


class ClaveInvalida(ObservatorioError):
    """La contrasena no descifra el archivo."""


def _derivar_clave(password: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        iterations=_ITER,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def cifrar(plano: bytes, password: str) -> bytes:
    return Fernet(_derivar_clave(password)).encrypt(plano)


def descifrar(token: bytes, password: str) -> bytes:
    try:
        return Fernet(_derivar_clave(password)).decrypt(token)
    except InvalidToken as e:
        raise ClaveInvalida("Contrasena incorrecta o archivo corrupto") from e
