"""Parser robusto de fechas heterogeneas a datetime tz-aware (UTC)."""
from __future__ import annotations

import re
from datetime import datetime, timezone

from dateutil import parser as dateutil_parser

_TIMESTAMP_UNIX = re.compile(r"^\d{10}(\.\d+)?$")
_TIMESTAMP_UNIX_MS = re.compile(r"^\d{13}$")


def parsear_fecha(crudo: str | int | float | datetime) -> datetime:
    """Acepta ISO 8601, timestamps unix (s o ms) y formatos comunes. Devuelve UTC."""
    if isinstance(crudo, datetime):
        return crudo if crudo.tzinfo else crudo.replace(tzinfo=timezone.utc)
    if isinstance(crudo, (int, float)):
        s = str(crudo)
    else:
        s = crudo.strip()

    if _TIMESTAMP_UNIX_MS.match(s):
        return datetime.fromtimestamp(int(s) / 1000, tz=timezone.utc)
    if _TIMESTAMP_UNIX.match(s):
        return datetime.fromtimestamp(float(s), tz=timezone.utc)

    dt = dateutil_parser.parse(s)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
