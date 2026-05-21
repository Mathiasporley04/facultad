"""Entrypoint de Streamlit para Observatorio Financiero LATAM."""
from __future__ import annotations

import sys
from pathlib import Path

# Permitir ejecutar `streamlit run src/observatorio/ui/app.py` sin instalar el paquete
_RAIZ = Path(__file__).resolve().parents[3]
_SRC = _RAIZ / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import streamlit as st  # noqa: E402

from observatorio.ui.vistas import comparar, panorama, portfolio  # noqa: E402

st.set_page_config(
    page_title="Observatorio Financiero LATAM",
    page_icon="📊",
    layout="wide",
)


def main() -> None:
    st.sidebar.title("Observatorio LATAM")
    st.sidebar.caption("Cripto · USA · Argentina · Uruguay")
    vista = st.sidebar.radio(
        "Vista",
        ["Panorama", "Comparar", "Mi Portfolio"],
        index=0,
    )

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "**Datos informativos.** No constituye asesoramiento financiero."
    )

    if vista == "Panorama":
        panorama.render()
    elif vista == "Comparar":
        comparar.render()
    else:
        portfolio.render()


if __name__ == "__main__":
    main()
else:
    main()
