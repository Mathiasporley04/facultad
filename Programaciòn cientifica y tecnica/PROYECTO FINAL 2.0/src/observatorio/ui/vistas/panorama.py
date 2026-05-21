"""Vista Panorama: snapshot de los cuatro mercados."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import plotly.graph_objects as go
import streamlit as st

from observatorio.core.excepciones import FuenteIndisponible
from observatorio.fuentes.coingecko import CoinGeckoAPI
from observatorio.fuentes.data912 import Data912API
from observatorio.fuentes.dolar_api_uy import DolarApiUY
from observatorio.fuentes.yahoo_finance import YahooFinanceAPI
from observatorio.metricas import normalizar_a_base


@st.cache_resource
def _fuentes():
    return {
        "cripto": CoinGeckoAPI(),
        "usa": YahooFinanceAPI(),
        "arg": Data912API(),
        "uy": DolarApiUY(),
    }


def _cotizar_seguro(fuente, simbolo: str, etiqueta: str) -> tuple[str, str]:
    try:
        c = fuente.precio_actual(simbolo)
        return f"{c.precio:,.2f} {c.moneda}", ""
    except FuenteIndisponible as e:
        return "—", f"{etiqueta} no disponible: {e}"


def render() -> None:
    st.title("Panorama de mercados")
    st.caption("Una vista rapida del estado de cuatro mercados relevantes para LATAM.")

    fuentes = _fuentes()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        valor, err = _cotizar_seguro(fuentes["uy"], "USD", "Dolar BROU")
        st.metric("Dolar (Uruguay)", valor)
        if err:
            st.caption(f":warning: {err}")

    with col2:
        valor, err = _cotizar_seguro(fuentes["cripto"], "BTC", "Bitcoin")
        st.metric("Bitcoin", valor)
        if err:
            st.caption(f":warning: {err}")

    with col3:
        valor, err = _cotizar_seguro(fuentes["usa"], "^GSPC", "S&P 500")
        st.metric("S&P 500", valor)
        if err:
            st.caption(f":warning: {err}")

    with col4:
        valor, err = _cotizar_seguro(fuentes["arg"], "GGAL", "GGAL (Merval)")
        st.metric("GGAL (Merval)", valor)
        if err:
            st.caption(f":warning: {err}")

    st.markdown("---")
    st.subheader("Comparativa normalizada (base 100)")
    periodo = st.selectbox("Periodo", ["7 dias", "30 dias", "90 dias"], index=1)
    dias = {"7 dias": 7, "30 dias": 30, "90 dias": 90}[periodo]
    hasta = datetime.now(timezone.utc)
    desde = hasta - timedelta(days=dias)

    series = {}

    try:
        btc = fuentes["cripto"].historico("BTC", desde, hasta)
        if btc:
            series["BTC"] = ([p.fecha for p in btc], [p.precio for p in btc])
    except FuenteIndisponible as e:
        st.caption(f":warning: BTC historico no disponible: {e}")

    try:
        spy = fuentes["usa"].historico("^GSPC", desde, hasta)
        if spy:
            series["S&P 500"] = ([p.fecha for p in spy], [p.precio for p in spy])
    except FuenteIndisponible as e:
        st.caption(f":warning: S&P 500 historico no disponible: {e}")

    if series:
        fig = go.Figure()
        for nombre, (fechas, precios) in series.items():
            normalizada = normalizar_a_base(precios, 100.0)
            fig.add_trace(go.Scatter(x=fechas, y=normalizada, mode="lines", name=nombre))
        fig.update_layout(
            xaxis_title="Fecha",
            yaxis_title="Indice (base 100)",
            margin=dict(l=10, r=10, t=30, b=10),
            height=420,
            legend=dict(orientation="h", y=-0.2),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No se pudieron obtener series historicas en este momento.")

    st.markdown("---")
    st.caption(
        "Datos provenientes de CoinGecko, Yahoo Finance, data912.com y DolarApi UY. "
        "Producto informativo, no constituye asesoramiento financiero."
    )
