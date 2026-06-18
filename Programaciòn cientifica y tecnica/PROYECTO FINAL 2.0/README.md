# Observatorio Financiero LATAM

Aplicacion Python que permite visualizar y comparar simultaneamente tres mercados financieros relevantes para un usuario latinoamericano: criptomonedas, bolsa estadounidense y cotizaciones de divisas en Uruguay (BROU).

> Producto **informativo y educativo**. **No constituye asesoramiento financiero.**

Ver `PROYECTO.md` para la especificacion tecnica completa.

## Instalacion

```bash
py -3 -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## Ejecutar

```bash
python -m observatorio.web
```

Luego abrir http://localhost:8000

En desarrollo, con autorecarga al editar:

```bash
uvicorn observatorio.web.app:app --reload
```

## Tests

```bash
pytest
```
