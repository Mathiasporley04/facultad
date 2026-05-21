"""Vista Mi Portfolio: carga, persiste cifrado y muestra distribucion.

V2: usa la clase `AlmacenCifrado`. Soporta import/export CSV y XML. Tabla
de tenencias con `precio_compra` para calcular PnL por posicion.
"""
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
    AlmacenCifrado,
    csv_a_tenencias,
    tenencias_a_csv,
    tenencias_a_xml,
    xml_a_tenencias,
)
from observatorio.persistencia.cifrado import ClaveInvalida

TIPOS = ["cripto", "usa", "arg", "uy"]


@st.cache_resource
def _almacen() -> AlmacenCifrado:
    return AlmacenCifrado()


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
        return 1.0 / c.precio if c.precio > 0 else None
    return None


def _obtener_tasas() -> tuple[float, float]:
    """Devuelve (tasa_ars_por_usd, tasa_uyu_por_usd)."""
    f = _fuentes()
    ars = uyu = 0.0
    try:
        uyu = f["uy"].precio_actual("USD").precio
    except FuenteIndisponible:
        pass
    return ars, uyu


def _normalizar(tenencias: list[dict]) -> list[dict]:
    """Garantiza presencia de `precio_compra` y descarta filas vacias."""
    salida = []
    for t in tenencias:
        sim = str(t.get("simbolo", "")).strip().upper()
        tipo = str(t.get("tipo", "")).strip().lower()
        cantidad = float(t.get("cantidad") or 0)
        if not sim or not tipo or cantidad <= 0:
            continue
        salida.append(
            {
                "simbolo": sim,
                "tipo": tipo,
                "cantidad": cantidad,
                "precio_compra": float(t.get("precio_compra") or 0.0),
            }
        )
    return salida


def _vista_login() -> None:
    almacen = _almacen()
    st.subheader("Mi Portfolio")
    if almacen.existe():
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
            return
        try:
            tenencias = almacen.cargar(pwd) if almacen.existe() else []
            st.session_state["portfolio_pwd"] = pwd
            st.session_state["portfolio_tenencias"] = tenencias
            st.rerun()
        except ClaveInvalida:
            st.error("Contrasena incorrecta.")


def _editor_tenencias(tenencias: list[dict]) -> list[dict]:
    df = (
        pd.DataFrame(tenencias)
        if tenencias
        else pd.DataFrame(columns=["simbolo", "tipo", "cantidad", "precio_compra"])
    )
    if "precio_compra" not in df.columns:
        df["precio_compra"] = 0.0
    edited = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "simbolo": st.column_config.TextColumn("Simbolo", required=True),
            "tipo": st.column_config.SelectboxColumn("Tipo", options=TIPOS, required=True),
            "cantidad": st.column_config.NumberColumn("Cantidad", min_value=0.0, step=0.0001),
            "precio_compra": st.column_config.NumberColumn(
                "Precio de compra (USD)",
                min_value=0.0,
                step=0.01,
                help="Opcional. Si lo cargas, podes ver la ganancia/perdida (PnL) por posicion.",
            ),
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
        "Tus tenencias se cifran con Fernet (AES-128 + HMAC-SHA256) via `AlmacenCifrado` "
        "y se guardan localmente. Producto informativo, **no constituye asesoramiento financiero**."
    )

    almacen = _almacen()
    pwd = st.session_state["portfolio_pwd"]
    tenencias = st.session_state.get("portfolio_tenencias", [])

    # --- barra de acciones (top) ---
    col_a, col_b, col_c, col_d = st.columns([1.4, 1, 1, 1])
    if col_a.button("Cerrar sesion (cifra y guarda)"):
        almacen.guardar(_normalizar(st.session_state["portfolio_tenencias"]), pwd)
        del st.session_state["portfolio_pwd"]
        del st.session_state["portfolio_tenencias"]
        st.rerun()

    csv_actual = tenencias_a_csv(tenencias)
    xml_actual = tenencias_a_xml(tenencias)
    col_b.download_button(
        "Exportar CSV", csv_actual, file_name="portfolio.csv", mime="text/csv"
    )
    col_c.download_button(
        "Exportar XML",
        xml_actual,
        file_name="portfolio.xml",
        mime="application/xml",
        help="Formato XML para integraciones con sistemas que lo requieren (directriz academica 7.1).",
    )

    archivo = col_d.file_uploader(
        "Importar CSV/XML",
        type=["csv", "xml"],
        label_visibility="collapsed",
    )
    if archivo is not None:
        contenido = archivo.getvalue().decode("utf-8")
        if archivo.name.lower().endswith(".xml"):
            nuevas = xml_a_tenencias(contenido)
        else:
            nuevas = csv_a_tenencias(contenido)
        if nuevas:
            st.session_state["portfolio_tenencias"] = nuevas
            st.success(f"Importadas {len(nuevas)} tenencias desde {archivo.name}.")
            st.rerun()
        else:
            st.warning(f"El archivo {archivo.name} no contiene tenencias validas.")

    st.markdown("### Tenencias")
    tenencias = _editor_tenencias(tenencias)
    st.session_state["portfolio_tenencias"] = tenencias

    if st.button("Guardar cambios", type="primary"):
        almacen.guardar(_normalizar(tenencias), pwd)
        st.success("Portfolio guardado y cifrado.")

    tenencias = _normalizar(tenencias)
    if not tenencias:
        st.info("Agrega al menos una tenencia para ver tu portfolio.")
        return

    # --- valuacion ---
    _, tasa_uyu = _obtener_tasas()
    valuadas = []
    for t in tenencias:
        precio = _precio_usd(t["tipo"], t["simbolo"], 1000.0, tasa_uyu)
        if precio is None:
            continue
        valor_usd = precio * float(t["cantidad"])
        precio_compra = float(t.get("precio_compra", 0.0))
        pnl_usd = (precio - precio_compra) * float(t["cantidad"]) if precio_compra > 0 else None
        valuadas.append(
            {
                **t,
                "precio_usd": precio,
                "valor_usd": valor_usd,
                "pnl_usd": pnl_usd,
            }
        )

    if not valuadas:
        st.warning("No se pudieron obtener precios de los activos cargados.")
        return

    total_usd = sum(v["valor_usd"] for v in valuadas)
    total_uyu = total_usd * tasa_uyu if tasa_uyu else 0.0
    pnl_total = sum((v["pnl_usd"] or 0) for v in valuadas)
    con_compra = [v for v in valuadas if v["pnl_usd"] is not None]

    st.markdown("### Valuacion total")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Valor total (USD)", f"$ {total_usd:,.2f}")
    c2.metric("Valor total (UYU)", f"$U {total_uyu:,.0f}" if total_uyu else "—")
    c3.metric("Posiciones", len(valuadas))
    if con_compra:
        c4.metric(
            "PnL acumulado (USD)",
            f"$ {pnl_total:,.2f}",
            delta=f"{(pnl_total / max(total_usd - pnl_total, 1e-9)) * 100:+.2f}%",
        )
    else:
        c4.caption("Carga precio de compra\npara ver PnL")

    # --- tabla de PnL por posicion ---
    if con_compra:
        st.markdown("### PnL por posicion")
        df_pnl = pd.DataFrame(
            [
                {
                    "Simbolo": v["simbolo"],
                    "Tipo": v["tipo"],
                    "Cantidad": v["cantidad"],
                    "Precio compra": v["precio_compra"],
                    "Precio actual": v["precio_usd"],
                    "Valor actual": v["valor_usd"],
                    "PnL (USD)": v["pnl_usd"],
                }
                for v in con_compra
            ]
        )
        st.dataframe(
            df_pnl,
            use_container_width=True,
            hide_index=True,
            column_config={
                "PnL (USD)": st.column_config.NumberColumn(format="$%.2f"),
                "Valor actual": st.column_config.NumberColumn(format="$%.2f"),
                "Precio compra": st.column_config.NumberColumn(format="$%.4f"),
                "Precio actual": st.column_config.NumberColumn(format="$%.4f"),
            },
        )

    # --- treemap distribucion ---
    st.markdown("### Distribucion del portfolio")
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
    st.caption(
        "Datos cifrados localmente con `AlmacenCifrado` (Fernet + PBKDF2). "
        "Producto informativo, no constituye asesoramiento financiero."
    )
