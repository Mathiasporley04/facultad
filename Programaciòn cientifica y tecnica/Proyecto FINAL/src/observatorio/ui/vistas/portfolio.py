"""Vista Mi Portfolio: carga, persiste cifrado y muestra distribucion."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from observatorio.core.excepciones import FuenteIndisponible
from observatorio.fuentes.coingecko import CoinGeckoAPI
from observatorio.fuentes.data912 import Data912API
from observatorio.fuentes.dolar_api_uy import DolarApiUY
from observatorio.fuentes.yahoo_finance import YahooFinanceAPI
from observatorio.persistencia.almacen import (
    cargar_portfolio,
    csv_a_tenencias,
    existe_portfolio,
    guardar_portfolio,
    tenencias_a_csv,
)
from observatorio.persistencia.cifrado import ClaveInvalida

TIPOS = ["cripto", "usa", "arg", "uy"]


@st.cache_resource
def _fuentes():
    return {
        "cripto": CoinGeckoAPI(),
        "usa": YahooFinanceAPI(),
        "arg": Data912API(),
        "uy": DolarApiUY(),
    }


def _precio_usd(tipo: str, simbolo: str, tasa_ars: float, tasa_uyu: float) -> float | None:
    f = _fuentes()
    try:
        c = f[tipo].precio_actual(simbolo)
    except (FuenteIndisponible, KeyError):
        return None
    if tipo in ("cripto", "usa"):
        return c.precio
    if tipo == "arg":
        return c.precio / tasa_ars if tasa_ars > 0 else None
    if tipo == "uy":
        # cotizacion de divisa => 1 unidad / cotizacion en UYU = USD
        return 1.0 / c.precio if c.precio > 0 else None
    return None


def _obtener_tasas() -> tuple[float, float]:
    """Devuelve (tasa_ars_por_usd, tasa_uyu_por_usd)."""
    f = _fuentes()
    ars = uyu = 0.0
    try:
        # Aproximacion: usamos USD oficial de UY como tasa UYU
        uyu = f["uy"].precio_actual("USD").precio
    except FuenteIndisponible:
        pass
    # ARS: aproximacion via UYU si no tenemos otra fuente
    return ars, uyu


def _vista_login() -> str | None:
    """Pide password. Devuelve password si el usuario confirma, None si no."""
    st.subheader("Mi Portfolio")
    if existe_portfolio():
        st.caption("Ya existe un portfolio guardado en disco. Ingresa la contrasena para abrirlo.")
    else:
        st.caption(
            "No hay portfolio guardado. Crea uno con una contrasena. "
            "Los datos se guardan **cifrados localmente** y nunca salen de tu maquina."
        )
    pwd = st.text_input("Contrasena", type="password", key="pwd_portfolio")
    if st.button("Abrir / Crear portfolio", type="primary"):
        if not pwd:
            st.error("Ingresa una contrasena.")
            return None
        try:
            tenencias = cargar_portfolio(pwd) if existe_portfolio() else []
            st.session_state["portfolio_pwd"] = pwd
            st.session_state["portfolio_tenencias"] = tenencias
            st.rerun()
        except ClaveInvalida:
            st.error("Contrasena incorrecta.")
    return None


def _editor_tenencias(tenencias: list[dict]) -> list[dict]:
    df = pd.DataFrame(tenencias) if tenencias else pd.DataFrame(
        columns=["simbolo", "tipo", "cantidad"]
    )
    edited = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "simbolo": st.column_config.TextColumn("Simbolo", required=True),
            "tipo": st.column_config.SelectboxColumn("Tipo", options=TIPOS, required=True),
            "cantidad": st.column_config.NumberColumn("Cantidad", min_value=0.0, step=0.0001),
        },
        key="editor_tenencias",
    )
    return edited.to_dict(orient="records")


def render() -> None:
    if "portfolio_pwd" not in st.session_state:
        _vista_login()
        return

    st.title("Mi Portfolio")
    st.caption(
        "Tus tenencias se cifran con Fernet (AES-128 + HMAC-SHA256) y se guardan localmente."
    )

    pwd = st.session_state["portfolio_pwd"]
    tenencias = st.session_state.get("portfolio_tenencias", [])

    col_a, col_b, col_c = st.columns([1, 1, 1])
    if col_a.button("Cerrar sesion (cifra y guarda)"):
        guardar_portfolio(st.session_state["portfolio_tenencias"], pwd)
        del st.session_state["portfolio_pwd"]
        del st.session_state["portfolio_tenencias"]
        st.rerun()

    csv_actual = tenencias_a_csv(tenencias)
    col_b.download_button(
        "Exportar CSV", csv_actual, file_name="portfolio.csv", mime="text/csv"
    )
    archivo = col_c.file_uploader("Importar CSV", type=["csv"], label_visibility="collapsed")
    if archivo is not None:
        nuevas = csv_a_tenencias(archivo.getvalue().decode("utf-8"))
        if nuevas:
            st.session_state["portfolio_tenencias"] = nuevas
            st.success(f"Importadas {len(nuevas)} tenencias. Guarda para persistir.")
            st.rerun()

    st.markdown("### Tenencias")
    tenencias = _editor_tenencias(tenencias)
    st.session_state["portfolio_tenencias"] = tenencias

    if st.button("Guardar cambios", type="primary"):
        guardar_portfolio(tenencias, pwd)
        st.success("Portfolio guardado y cifrado.")

    if not tenencias:
        st.info("Agrega al menos una tenencia para ver tu portfolio.")
        return

    # Valuacion
    _, tasa_uyu = _obtener_tasas()
    valuadas = []
    for t in tenencias:
        precio = _precio_usd(t["tipo"], t["simbolo"], 1000.0, tasa_uyu)
        if precio is None:
            continue
        valor_usd = precio * float(t["cantidad"])
        valuadas.append({**t, "precio_usd": precio, "valor_usd": valor_usd})

    if not valuadas:
        st.warning("No se pudieron obtener precios de los activos cargados.")
        return

    total_usd = sum(v["valor_usd"] for v in valuadas)
    total_uyu = total_usd * tasa_uyu if tasa_uyu else 0.0

    st.markdown("### Valuacion total")
    c1, c2, c3 = st.columns(3)
    c1.metric("Valor total (USD)", f"$ {total_usd:,.2f}")
    c2.metric("Valor total (UYU)", f"$U {total_uyu:,.0f}" if total_uyu else "—")
    c3.metric("Posiciones", len(valuadas))

    # Treemap distribucion
    df_v = pd.DataFrame(valuadas)
    fig = px.treemap(
        df_v,
        path=[px.Constant("Portfolio"), "tipo", "simbolo"],
        values="valor_usd",
        color="tipo",
    )
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.caption("Datos cifrados localmente. Producto informativo, no constituye asesoramiento financiero.")
