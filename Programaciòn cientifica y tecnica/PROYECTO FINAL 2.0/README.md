# Observatorio Financiero LATAM

Aplicacion Python que permite visualizar y comparar simultaneamente cuatro mercados financieros relevantes para un usuario latinoamericano: criptomonedas, bolsa estadounidense, bolsa argentina y cotizaciones de divisas en Uruguay (BROU).

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
streamlit run src/observatorio/ui/app.py
```

Luego abrir http://localhost:8501

## Tests

```bash
pytest
```
