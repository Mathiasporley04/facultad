"""Persistencia del portfolio cifrado en disco.

V2: la API principal es la clase `AlmacenCifrado`. Las funciones libres se
mantienen como wrappers thin para compatibilidad con la UI y los tests.
"""
from __future__ import annotations

import base64
import csv
import io
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .cifrado import ClaveInvalida

_DEFAULT_PATH = Path("data/portfolio/portfolio.enc")
_DEFAULT_SALT = b"observatorio-latam-v1"
_DEFAULT_ITER = 200_000


class AlmacenCifrado:
    """Encapsula la persistencia cifrada del portfolio en disco.

    Atributos:
        ruta: archivo `.enc` donde se guarda el JSON cifrado.
        salt: sal para PBKDF2. Default: salt fijo del proyecto (mono-usuario).
        iteraciones: iteraciones de PBKDF2-SHA256.

    Las primitivas criptograficas (`_derivar_clave`, `_cifrar`, `_descifrar`) son
    metodos protegidos. La API publica son `guardar`, `cargar`, `existe`.
    """

    def __init__(
        self,
        ruta: Path | str = _DEFAULT_PATH,
        salt: bytes = _DEFAULT_SALT,
        iteraciones: int = _DEFAULT_ITER,
    ) -> None:
        self.ruta = Path(ruta)
        self.salt = salt
        self.iteraciones = iteraciones

    # ---------- API publica ----------

    def existe(self) -> bool:
        return self.ruta.exists()

    def guardar(self, tenencias: list[dict], password: str) -> None:
        """Cifra `tenencias` (lista de dicts JSON-serializables) y escribe en `ruta`."""
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        plano = json.dumps(tenencias, ensure_ascii=False).encode("utf-8")
        token = self._cifrar(plano, password)
        self.ruta.write_bytes(token)

    def cargar(self, password: str) -> list[dict]:
        """Descifra el archivo y devuelve la lista de tenencias. Lanza `ClaveInvalida`
        si la contrasena es incorrecta."""
        if not self.existe():
            return []
        token = self.ruta.read_bytes()
        plano = self._descifrar(token, password)
        return json.loads(plano.decode("utf-8"))

    # ---------- primitivas protegidas ----------

    def _derivar_clave(self, password: str) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=self.iteraciones,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))

    def _cifrar(self, plano: bytes, password: str) -> bytes:
        return Fernet(self._derivar_clave(password)).encrypt(plano)

    def _descifrar(self, token: bytes, password: str) -> bytes:
        try:
            return Fernet(self._derivar_clave(password)).decrypt(token)
        except InvalidToken as e:
            raise ClaveInvalida("Contrasena incorrecta o archivo corrupto") from e


# ============================================================
# Wrappers legacy (compat con la UI y tests pre-V2)
# ============================================================

def guardar_portfolio(tenencias: list[dict], password: str, path: Path = _DEFAULT_PATH) -> None:
    AlmacenCifrado(ruta=path).guardar(tenencias, password)


def cargar_portfolio(password: str, path: Path = _DEFAULT_PATH) -> list[dict]:
    return AlmacenCifrado(ruta=path).cargar(password)


def existe_portfolio(path: Path = _DEFAULT_PATH) -> bool:
    return AlmacenCifrado(ruta=path).existe()


# ============================================================
# Serializadores CSV
# ============================================================

_CAMPOS_CSV = ["simbolo", "tipo", "cantidad", "precio_compra"]


def tenencias_a_csv(tenencias: list[dict]) -> str:
    if not tenencias:
        return ",".join(_CAMPOS_CSV) + "\n"
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_CAMPOS_CSV, extrasaction="ignore")
    writer.writeheader()
    for t in tenencias:
        writer.writerow(
            {
                "simbolo": t["simbolo"],
                "tipo": t["tipo"],
                "cantidad": t["cantidad"],
                "precio_compra": t.get("precio_compra", 0.0),
            }
        )
    return buf.getvalue()


def csv_a_tenencias(texto: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(texto))
    salida = []
    for fila in reader:
        try:
            registro = {
                "simbolo": fila["simbolo"].strip().upper(),
                "tipo": fila["tipo"].strip().lower(),
                "cantidad": float(fila["cantidad"]),
            }
            if "precio_compra" in fila and fila["precio_compra"]:
                registro["precio_compra"] = float(fila["precio_compra"])
            salida.append(registro)
        except (KeyError, ValueError):
            continue
    return salida


# ============================================================
# Serializadores XML (directriz 7.1 — formato XML)
# ============================================================


def tenencias_a_xml(tenencias: list[dict]) -> str:
    """Serializa tenencias a XML.

    Estructura:
        <portfolio>
            <tenencia simbolo="BTC" tipo="cripto">
                <cantidad>0.5</cantidad>
                <precio_compra>30000.0</precio_compra>
            </tenencia>
            ...
        </portfolio>
    """
    raiz = ET.Element("portfolio")
    for t in tenencias:
        elem = ET.SubElement(
            raiz,
            "tenencia",
            attrib={"simbolo": str(t["simbolo"]), "tipo": str(t["tipo"])},
        )
        ET.SubElement(elem, "cantidad").text = str(t["cantidad"])
        ET.SubElement(elem, "precio_compra").text = str(t.get("precio_compra", 0.0))
    ET.indent(raiz, space="  ")
    return ET.tostring(raiz, encoding="unicode", xml_declaration=True)


def xml_a_tenencias(texto: str) -> list[dict]:
    """Parsea XML producido por `tenencias_a_xml` y devuelve la lista de dicts.

    Robusto a `precio_compra` faltante (default 0.0) y a elementos extra (ignorados).
    """
    try:
        raiz = ET.fromstring(texto)
    except ET.ParseError:
        return []
    salida: list[dict] = []
    for elem in raiz.findall("tenencia"):
        simbolo = elem.get("simbolo", "").strip().upper()
        tipo = elem.get("tipo", "").strip().lower()
        if not simbolo or not tipo:
            continue
        cantidad_text = (elem.findtext("cantidad") or "").strip()
        precio_text = (elem.findtext("precio_compra") or "0").strip()
        try:
            cantidad = float(cantidad_text)
            precio_compra = float(precio_text) if precio_text else 0.0
        except ValueError:
            continue
        salida.append(
            {
                "simbolo": simbolo,
                "tipo": tipo,
                "cantidad": cantidad,
                "precio_compra": precio_compra,
            }
        )
    return salida
