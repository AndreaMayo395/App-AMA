# ───────────────────────────────────────────────────────────────────────────────
# PESTAÑA: 📊 Exploración de Datos  (SOLO CSVs locales del usuario)
# Reqs: pip install streamlit pandas numpy
# ───────────────────────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import numpy as np

# =========================== HELPERS / CACHES ==================================
@st.cache_data
def load_yahoo_csv(file_or_buffer) -> pd.DataFrame:
    """
    Carga un CSV de Yahoo Finance (AMZN/ORCL) con columnas:
    Date, Open, High, Low, Close, Adj Close, Volume
    Devuelve DataFrame indexado por Date (datetime), ordenado ascendente.
    """
    df = pd.read_csv(file_or_buffer)
    # Normalizar nombres por si vienen capitalizaciones raras
    df.columns = [c.strip().title() for c in df.columns]
    # Filtrar filas “Dividend” / “Stock Split” si vinieran en otros formatos
    if "Open" not in df.columns and "Adj Close" not in df.columns and "Close" not in df.columns:
        raise ValueError("El CSV no parece de Yahoo (faltan columnas de precio).")
    # Convertir fecha
    if "Date" not in df.columns:
        raise ValueError("El CSV debe tener columna 'Date'.")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values("Date").set_index("Date")

    # Convertir numéricas
    for c in ["Open","High","Low","Close","Adj Close","Volume"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    # Eliminar filas vacías de mercado cerrado, etc.
    df = df.dropna(subset=[c for c in ["Close","Adj Close"] if c in df.columns], how="all")
    return df

@st.cache_data
def load_btc_csv(file_or_buffer) -> pd.DataFrame:
    """
    Carga BTC desde:
    - CSV de trades (Binance/aggTrades): columnas como time, price, qty, base_qty...
    - CSV de klines (Binance): open_time, open, high, low, close, volume ...
    - CSV EOD (CryptoDataDownload / CoinGecko): Date + Close (u OHLC)
    Devuelve SIEMPRE un DataFrame OHLCV con índice datetime ascendente.
    """
    df = pd.read_csv(file_or_buffer)
    cols_lower = {c: c.lower().strip() for c in df.columns}
    df.rename(columns=cols_lower, inplace=True)

    # 1) Formato KLINES (Binance)
    if "open_time" in df.columns and "close" in df.columns:
        # Toma open_time (ms) como índice
        ts = pd.to_datetime(df["open_time"], unit="ms", errors="coerce").dt.tz_localize(None)
        out = pd.DataFrame({
            "Open": pd.to_numeric(df.get("open"), errors="coerce"),
            "High": pd.to_numeric(df.get("high"), errors="coerce"),
            "Low": pd.to_numeric(df.get("low"), errors="coerce"),
            "Close": pd.to_numeric(df.get("close"), errors="coerce"),
            "Volume": pd.to_numeric(df.get("volume"), errors="coerce"),
        }, index=ts)
        out = out.dropna(subset=["Close"]).sort_index()
        return out

    # 2) Formato TRADES (price/qty/time en ms) → agregamos a 1D
    if {"price","qty","time"}.issubset(df.columns):
        df["time"] = pd.to_datetime(df["time"], unit="ms", errors="coerce").dt.tz_localize(None)
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df["qty"]   = pd.to_numeric(df["qty"], errors="coerce")
        df = df.dropna(subset=["time","price","qty"]).sort_values("time").set_index("time")
        # Resample diario a OHLCV + VWAP
        ohlc = df["price"].resample("1D").agg(["first","max","min","last"])
        ohlc.columns = ["Open","High","Low","Close"]
        vol = df["qty"].resample("1D").sum().rename("Volume")
        vwap = (df["price"]*df["qty"]).resample("1D").sum() / df["qty"].resample("1D").sum()
        out = pd.concat([ohlc, vol, vwap.rename("VWAP")], axis=1).dropna(how="all")
        return out

    # 3) Formato EOD genérico (CryptoDataDownload / CoinGecko)
    # Buscamos columnas de fecha y cierre
    cand_date = next((c for c in df.columns if c in ["date","timestamp","time"]), None)
    cand_close = next((c for c in df.columns if c in ["close","adj close","price","last"]), None)
    if cand_date and cand_close:
        ts = pd.to_datetime(df[cand_date], errors="coerce")
        close = pd.to_numeric(df[cand_close], errors="coerce")
        open_  = pd.to_numeric(df.get("open"), errors="coerce")
        high   = pd.to_numeric(df.get("high"), errors="coerce")
        low    = pd.to_numeric(df.get("low"), errors="coerce")
        vol    = pd.to_numeric(df.get("volume"), errors="coerce")
        out = pd.DataFrame({"Open":open_,"High":high,"Low":low,"Close":close,"Volume":vol}, index=ts)
        out.index = pd.to_datetime(out.index).tz_localize(None)
        out = out.dropna(subset=["Close"]).sort_index()
        return out

    raise ValueError("No reconozco el formato del CSV de BTC (esperaba klines, trades o EOD con Date/Close).")

def quick_stats(df: pd.DataFrame, price_col="Close"):
    ret = df[price_col].pct_change().dropna()
    st.write(pd.DataFrame({
        "Observaciones": [len(df)],
        "Retorno medio": [ret.mean()],
        "Volatilidad": [ret.std()],
        "Retorno acumulado": [(df[price_col].iloc[-1]/df[price_col].iloc[0]-1) if len(df)>1 else np.nan]
    }).T.rename(columns={0:""}))

def df_download_button(df, filename: str, label: str = "📥 Descargar CSV"):
    csv = df.to_csv(index=True).encode("utf-8")
    st.download_button(label, data=csv, file_name=filename, mime="text/csv")

st.sidebar.title("🧭 Navegación")
pagina = st.sidebar.radio(
    "Selecciona un módulo:",
    (
        "🏠 Inicio",
        "📊 Exploración de Datos",
        "📈 Análisis de Portafolio",
        "💵 Perfil de Riesgo",
        "🧮 Ajustar la estrategia de Inversión"
    )
)


if pagina == "🏠 Inicio":
    st.set_page_config(page_title="Dashboard Financiero 💹", layout="wide")


    # Estructura inicial — luego se reemplazará con datos de criptomonedas, es un bosquejo de las gráfica para hacer
    activos = ["Activo 1", "Activo 2", "Activo 3", "Activo 4", "Activo 5"]

    data = pd.DataFrame({
        "Activo": activos,
        "Peso": [np.nan] * len(activos),
        "Rendimiento": [np.nan] * len(activos),
        "Riesgo": [np.nan] * len(activos)
    })

    #Este apartado va a ser de para visualizar el desempeño que se tiene, con las medidas más importantes
    st.title("Dashboard Financiero")
    st.caption("Visualiza el desempeño general de tu portafolio de inversión")

    col1, col2, col3 = st.columns(3)
    col1.metric("Rendimiento Promedio", "-- %")
    col2.metric("Riesgo Promedio", "-- %")
    col3.metric("Ratio Sharpe Medio", "-- %")

    #Algunos de los gráficos a realizar para el portafolio, para que el usuario pueda visualizar distribuciones y rendimientos
    st.subheader("📊 Distribución del Portafolio")
    st.bar_chart(pd.DataFrame([], columns=["Peso"])) 

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📈 Rendimiento por Activo")
        st.bar_chart(pd.DataFrame([], columns=["Rendimiento"]))

    with col2:
        st.subheader("⚠️ Riesgo por Activo")
        st.bar_chart(pd.DataFrame([], columns=["Riesgo"]))

    # COn este apartado se piensa ver cómo evoluviona 
    st.subheader("📉 Evolución del Portafolio en el Tiempo")
    st.line_chart(pd.DataFrame([], columns=["Valor Portafolio"]))

    st.markdown("---")
    st.caption("© 2025 Dashboard Financiero - Hecho por Andrea Mayorga")

# ============================ PÁGINA / UI ======================================
elif pagina == "📊 Exploración de Datos":
    st.title("📊 Exploración de Datos (CSV locales)")

    # -------------------- 1) BITCOIN DESDE TU CSV ------------------------------
    st.subheader("1) Bitcoin desde CSV (detecta formato automáticamente)")
    btc_file = st.file_uploader("Sube tu CSV de BTC (klines/trades/EOD)", type=["csv"], key="btc_csv")
    price_to_plot = st.radio("Precio a graficar (BTC)", ["Close","VWAP"], horizontal=True, index=0)

    if btc_file is not None:
        try:
            btc_df = load_btc_csv(btc_file)
            st.success(f"BTC cargado · {btc_df.index.min()} → {btc_df.index.max()} · {len(btc_df):,} filas")
            st.dataframe(btc_df.tail(20), use_container_width=True)
            col = price_to_plot if price_to_plot in btc_df.columns else "Close"
            st.line_chart(btc_df[[col]].dropna(), height=280, use_container_width=True)
            with st.expander("Estadísticas rápidas (BTC)"):
                quick_stats(btc_df, price_col="Close")
            df_download_button(btc_df, "BTC_clean_OHLCV.csv", "📥 Descargar BTC (limpio)")
        except Exception as e:
            st.error(f"Error cargando BTC: {e}")
    else:
        st.info("Sube tu CSV de BTC para visualizarlo.")

    st.markdown("---")

    # -------------------- 2) AMZN / ORCL DESDE TUS CSVs ------------------------
    st.subheader("2) Acciones desde CSV (Yahoo Finance recomendado)")
    c1, c2 = st.columns(2)
    amzn_file = c1.file_uploader("Sube AMZN (CSV)", type=["csv"], key="amzn_csv")
    orcl_file = c2.file_uploader("Sube ORCL (CSV)", type=["csv"], key="orcl_csv")

    def render_equity_block(name: str, fileobj):
        st.write(f"### {name}")
        if fileobj is None:
            st.info("Sube el CSV para visualizar.")
            return
        try:
            df = load_yahoo_csv(fileobj)
            st.success(f"{name} cargado · {df.index.min().date()} → {df.index.max().date()} · {len(df):,} filas")
            st.dataframe(df.tail(20), use_container_width=True)
            price_col = "Adj Close" if "Adj Close" in df.columns and df["Adj Close"].notna().any() else "Close"
            st.line_chart(df[[price_col]].dropna(), height=260, use_container_width=True)
            with st.expander(f"Estadísticas rápidas ({name})"):
                quick_stats(df, price_col)
            df_download_button(df, f"{name}_clean.csv", f"📥 Descargar {name} (limpio)")
        except Exception as e:
            st.error(f"Error con {name}: {e}")

    render_equity_block("AMZN", amzn_file)
    render_equity_block("ORCL", orcl_file)

    st.markdown("---")
    st.info("Consejo: para retornos de acciones usa **Adj Close** (si está); para BTC, **Close** o **VWAP**.\n"
            "Con estos CSV ya puedes pasar a la pestaña de portafolio sin depender de ninguna API.")
