"""Vista Comparar: analisis profundo entre activos."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from observatorio.core.excepciones import FuenteIndisponible
from observatorio.fuentes.coingecko import CoinGeckoAPI
from observatorio.fuentes.yahoo_finance import YahooFinanceAPI
from observatorio.metricas import (
    calcular_drawdown_maximo,
    calcular_rendimiento_porcentual,
    calcular_volatilidad,
    clasificar_volatilidad,
    matriz_correlacion,
    normalizar_a_base,
)
from observatorio.ui.glosario import GLOSARIO

# Universos comparables (con historico real)
UNIVERSO: dict[str, tuple[str, str]] = {
    "BTC (Bitcoin)": ("cripto", "BTC"),
    "ETH (Ethereum)": ("cripto", "ETH"),
    "SOL (Solana)": ("cripto", "SOL"),
    "AAPL (Apple)": ("usa", "AAPL"),
    "MSFT (Microsoft)": ("usa", "MSFT"),
    "GOOGL (Alphabet)": ("usa", "GOOGL"),
    "TSLA (Tesla)": ("usa", "TSLA"),
    "NVDA (Nvidia)": ("usa", "NVDA"),
    "S&P 500 (^GSPC)": ("usa", "^GSPC"),
}


@st.cache_resource
def _fuentes():
    return {"cripto": CoinGeckoAPI(), "usa": YahooFinanceAPI()}


@st.cache_data(ttl=3600, show_spinner=False)
def _obtener_serie(clave_fuente: str, simbolo: str, dias: int) -> tuple[list, list]:
    fuentes = _fuentes()
    hasta = datetime.now(timezone.utc)
    desde = hasta - timedelta(days=dias)
    try:
        puntos = fuentes[clave_fuente].historico(simbolo, desde, hasta)
    except FuenteIndisponible:
        return [], []
    return [p.fecha for p in puntos], [p.precio for p in puntos]


def render() -> None:
    st.title("Comparar activos")
    st.caption(
        "Seleccionar dos o mas activos para compararlos en rendimiento, "
        "volatilidad y correlacion."
    )

    seleccion = st.multiselect(
        "Activos a comparar",
        options=list(UNIVERSO.keys()),
        default=["BTC (Bitcoin)", "S&P 500 (^GSPC)"],
    )
    periodo = st.selectbox("Periodo", ["30 dias", "90 dias", "180 dias", "1 año"], index=1)
    dias = {"30 dias": 30, "90 dias": 90, "180 dias": 180, "1 año": 365}[periodo]

    if len(seleccion) < 1:
        st.info("Seleccionar al menos un activo.")
        return

    # Recolectar series
    series_precios: dict[str, list[float]] = {}
    series_fechas: dict[str, list] = {}
    errores: list[str] = []
    for label in seleccion:
        clave, simbolo = UNIVERSO[label]
        fechas, precios = _obtener_serie(clave, simbolo, dias)
        if precios:
            series_precios[label] = precios
            series_fechas[label] = fechas
        else:
            errores.append(label)

    if errores:
        st.caption(f":warning: Sin datos: {', '.join(errores)}")

    if not series_precios:
        st.warning("No se pudo obtener ninguna serie.")
        return

    # Grafico normalizado base 100
    st.subheader(f"Evolucion normalizada (base 100, ultimos {periodo})")
    st.caption(GLOSARIO["base_100"])
    fig = go.Figure()
    for label, precios in series_precios.items():
        norm = normalizar_a_base(precios, 100.0)
        fig.add_trace(go.Scatter(x=series_fechas[label], y=norm, mode="lines", name=label))
    fig.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", y=-0.2),
        yaxis_title="Indice (base 100)",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tabla de metricas
    st.subheader("Metricas por activo")
    filas = []
    for label, precios in series_precios.items():
        rend = calcular_rendimiento_porcentual(precios[0], precios[-1])
        vol = calcular_volatilidad(precios)
        dd = calcular_drawdown_maximo(precios)
        filas.append(
            {
                "Activo": label,
                "Rendimiento %": round(rend, 2),
                "Volatilidad anual": round(vol, 3),
                "Clasificacion": clasificar_volatilidad(vol),
                "Peor caida %": round(dd * 100, 2),
            }
        )
    df = pd.DataFrame(filas)
    st.dataframe(df, use_container_width=True, hide_index=True)
    with st.expander("¿Que significan estas metricas?"):
        st.markdown(
            f"- **Rendimiento %**: {GLOSARIO['rendimiento']}\n"
            f"- **Volatilidad**: {GLOSARIO['volatilidad']}\n"
            f"- **Peor caida %**: {GLOSARIO['drawdown']}"
        )

    # Heatmap de correlaciones
    if len(series_precios) >= 2:
        st.subheader("Correlacion entre activos")
        st.caption(GLOSARIO["correlacion"])
        m = matriz_correlacion(series_precios)
        labels = list(m.keys())
        z = [[m[a][b] for b in labels] for a in labels]
        heat = px.imshow(
            z,
            x=labels,
            y=labels,
            color_continuous_scale="RdYlGn",
            zmin=-1,
            zmax=1,
            text_auto=".2f",
            aspect="auto",
        )
        heat.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(heat, use_container_width=True)

    st.markdown("---")
    st.caption(
        "Rendimientos pasados no garantizan rendimientos futuros. "
        "Producto informativo, no constituye asesoramiento financiero."
    )
