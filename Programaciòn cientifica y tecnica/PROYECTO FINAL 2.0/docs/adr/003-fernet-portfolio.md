# ADR-003: Cifrado de portfolio con Fernet

**Estado:** aceptado.

## Contexto
El modo "Mi Portfolio" persiste tenencias del usuario en disco. Aunque no hay datos identificatorios, la informacion economica es sensible.

## Opciones evaluadas
1. **Fernet** (libreria `cryptography`): wrapper alto nivel sobre AES-128-CBC + HMAC-SHA256.
2. **AES-GCM directo**: mas moderno pero requiere mas codigo defensivo (nonce, tag, etc).
3. **SQLCipher**: cifra una base SQLite entera. Mas dependencias, overkill para JSON pequeno.

## Decision
**Fernet** con clave derivada de password via PBKDF2-SHA256 (200_000 iteraciones, salt fijo del proyecto).

## Razones
- API de alto nivel: `cifrar(plano, password) -> token`, `descifrar(token, password) -> plano`. Dificil de usar mal.
- Token autenticado (HMAC) detecta corrupcion / contrasena incorrecta.
- Formato versionado: futuro upgrade no rompe archivos existentes.

## Consecuencias
- AES-128 (no 256). Suficiente para amenaza local.
- Salt fijo: la herramienta es de un solo usuario por instalacion. Aceptable.
- Modelo de amenaza explicito en `docs/etica.md`.
