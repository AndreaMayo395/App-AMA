import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, date

st.set_page_config(page_title="Análisis de Portafolio 💹", page_icon="💸", layout="wide")



# =========================== HELPERS / CACHES ==================================
@st.cache_data
def load_binance_trades_csv(file_or_path):
    """
    Lee CSV de trades: id, price, qty, base_qty, time, is_buyer_maker
    Convierte time (ms) → datetime, y deja índice temporal.
    """
    df = pd.read_csv(file_or_path)
    df = df.rename(columns={c: c.lower() for c in df.columns})

    if not {"price", "qty", "time"}.issubset(df.columns):
        raise ValueError("Se requieren columnas al menos: price, qty, time")

    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["qty"]   = pd.to_numeric(df["qty"], errors="coerce")
    if "base_qty" in df.columns:
        df["base_qty"] = pd.to_numeric(df["base_qty"], errors="coerce")
    else:
        df["base_qty"] = df["price"] * df["qty"]

    df["time"] = pd.to_datetime(df["time"], unit="ms", errors="coerce").dt.tz_localize(None)
    df = df.dropna(subset=["time","price","qty"]).sort_values("time").set_index("time")
    df = df.rename(columns={"id":"trade_id","is_buyer_maker":"isBuyerMaker"})
    return df

def trades_to_ohlcv(trades_df, rule="1D"):
    """
    Agrega trades → OHLCV por intervalo (1T/1H/1D) y calcula VWAP.
    Volume = Σ qty (activo base).
    """
    ohlc = trades_df["price"].resample(rule).agg(["first","max","min","last"])
    ohlc.columns = ["Open","High","Low","Close"]
    volume = trades_df["qty"].resample(rule).sum().rename("Volume")
    vwap = (trades_df["price"]*trades_df["qty"]).resample(rule).sum() / trades_df["qty"].resample(rule).sum()
    vwap = vwap.rename("VWAP")
    out = pd.concat([ohlc, volume, vwap], axis=1).dropna(how="all")
    return out

@st.cache_data
def fetch_yahoo_ohlcv(ticker: str, start: date, end: date, interval: str = "1d") -> pd.DataFrame:
    """
    Descarga OHLCV (y Adj Close) desde Yahoo v8 chart sin yfinance.
    interval: '1d','1wk','1mo'
    """
    # period1 = inicio 00:00:00, period2 = fin 23:59:59
    p1 = int(pd.Timestamp(start).tz_localize("UTC").timestamp())
    p2 = int(pd.Timestamp(end) .tz_localize("UTC").timestamp())

    url = "https://query1.finance.yahoo.com/v8/finance/chart/{}".format(ticker)
    params = {
        "period1": p1,
        "period2": p2,
        "interval": interval,
        "events": "div,split",
        "includePrePost": "false"
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    js = r.json()

    # Navegar el JSON
    res = js.get("chart", {}).get("result", [])
    if not res:
        raise ValueError(f"Yahoo no devolvió datos para {ticker}.")
    res = res[0]
    timestamps = res.get("timestamp", [])
    if not timestamps:
        raise ValueError(f"Sin timestamps para {ticker}.")

    q = res["indicators"]["quote"][0]
    opens  = q.get("open", [])
    highs  = q.get("high", [])
    lows   = q.get("low", [])
    closes = q.get("close", [])
    vols   = q.get("volume", [])
    # adj close (si está)
    adj = res["indicators"].get("adjclose", [{}])[0].get("adjclose", [None]*len(timestamps))

    idx = pd.to_datetime(pd.Series(timestamps), unit="s", utc=True).dt.tz_localize(None)
    df = pd.DataFrame({
        "Open": opens,
        "High": highs,
        "Low": lows,
        "Close": closes,
        "Adj Close": adj,
        "Volume": vols
    }, index=idx).dropna(how="all")

    # Ordenar y filtrar por fechas exactas por si Yahoo trae márgenes
    df = df.sort_index()
    df = df.loc[(df.index.date >= start) & (df.index.date <= end)]
    if df.empty:
        raise ValueError(f"Yahoo devolvió DataFrame vacío para {ticker} en el rango seleccionado.")
    return df

def quick_stats(df: pd.DataFrame, price_col="Close"):
    ret = df[price_col].pct_change().dropna()
    st.write(pd.DataFrame({
        "Observaciones": [len(df)],
        "Retorno medio (periodo)": [ret.mean()],
        "Volatilidad (periodo)": [ret.std()],
        "Retorno acumulado": [(df[price_col].iloc[-1]/df[price_col].iloc[0]-1) if len(df)>1 else np.nan]
    }).T.rename(columns={0:""}))

def df_download_button(df, filename: str, label: str = "📥 Descargar CSV"):
    csv = df.to_csv(index=True).encode("utf-8")
    st.download_button(label, data=csv, file_name=filename, mime="text/csv")



# =============================
# MENÚ LATERAL
# =============================
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




elif pagina == "📊 Exploración de Datos":
    st.title("📊 Exploración de Datos")

    # -------------------- 1) BITCOIN DESDE CSV (TRADES → VELAS) ----------------
    st.subheader("1) Bitcoin desde CSV (trades → velas)")
    st.caption("Sube tu CSV con columnas como: id, price, qty, base_qty, time (ms), is_buyer_maker.")

    btc_trades_file = st.file_uploader("Sube CSV de trades (BTC/USDT, etc.)", type=["csv"], key="btc_trades")
    rule_label = st.selectbox("Intervalo de agregación", ["1T (1 minuto)","1H (1 hora)","1D (1 día)"], index=2)
    rule = {"1T (1 minuto)":"1T","1H (1 hora)":"1H","1D (1 día)":"1D"}[rule_label]
    price_to_plot = st.radio("Precio a graficar", ["Close","VWAP"], horizontal=True, index=0)

    if btc_trades_file is not None:
        try:
            trades_df = load_binance_trades_csv(btc_trades_file)
            st.success(f"Trades cargados: {len(trades_df):,} filas · rango: {trades_df.index.min()} → {trades_df.index.max()}")
            with st.expander("Muestra de trades (primeras 20 filas)"):
                st.dataframe(trades_df.head(20), use_container_width=True)

            btc_ohlcv = trades_to_ohlcv(trades_df, rule=rule)
            st.write(f"### Velas BTC ({rule_label})")
            st.dataframe(btc_ohlcv.tail(20), use_container_width=True)

            col_to_plot = price_to_plot if price_to_plot in btc_ohlcv.columns else "Close"
            st.line_chart(btc_ohlcv[[col_to_plot]].dropna(), height=280, use_container_width=True)

            with st.expander("Estadísticas rápidas (BTC)"):
                quick_stats(btc_ohlcv, price_col="Close")
            df_download_button(btc_ohlcv, f"btc_ohlcv_{rule}.csv", "📥 Descargar velas BTC (CSV)")
        except Exception as e:
            st.error(f"Error con el CSV de BTC: {e}")
    else:
        st.info("Sube el CSV para ver precio y velas de BTC.")

    st.markdown("---")

    # -------------------- 2) ACCIONES (AMZN / ORCL) DESDE YAHOO (requests) -----
    st.subheader("2) Acciones (AMZN / ORCL) desde Yahoo (sin yfinance)")
    st.caption("Descarga directa vía API pública v8 chart. Filtra por fechas.")

    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        start_date = st.date_input("Desde", pd.to_datetime("2018-01-01").date(), key="yh_start")
    with c2:
        end_date = st.date_input("Hasta", pd.Timestamp.today().date(), key="yh_end")
    with c3:
        interval = st.selectbox("Intervalo", ["1d","1wk","1mo"], index=0)

    for tk in ["AMZN", "ORCL"]:
        st.write(f"### {tk}")
        try:
            df_yh = fetch_yahoo_ohlcv(tk, start_date, end_date, interval=interval)
            st.dataframe(df_yh.tail(20), use_container_width=True)

            price_col = "Adj Close" if "Adj Close" in df_yh.columns and df_yh["Adj Close"].notna().any() else "Close"
            st.line_chart(df_yh[[price_col]].dropna(), height=260, use_container_width=True)

            with st.expander(f"Estadísticas rápidas ({tk})"):
                quick_stats(df_yh, price_col)

            df_download_button(df_yh, f"{tk}_yahoo_{start_date}_{end_date}_{interval}.csv",
                               f"📥 Descargar {tk} (CSV)")
        except Exception as e:
            st.error(f"No pude traer {tk} desde Yahoo: {e}")

    st.markdown("---")
    st.info("Notas: Yahoo v8 chart permite obtener OHLCV y Adj Close sin yfinance. "
            "Para portafolios, usa **Adj Close** si está disponible; si no, **Close**.")


elif pagina == "📈 Análisis de Portafolio":
    st.title("📈 Análisis de Portafolio")
    
elif pagina == "💵 Perfil de Riesgo":
    st.title("💵 Perfil de Riesgo")
    
elif pagina == "🧮 Estrategia":
    st.title("🧮 Ajustar la estrategia de Inversión")


