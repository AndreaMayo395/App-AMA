# ───────────────────────────────────────────────────────────────────────────────
# PESTAÑA: 📊 Exploración de Datos  (BTC desde CSV; AMZN/ORCL desde Alpha Vantage)
# Reqs: pip install streamlit pandas numpy requests
# ───────────────────────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import numpy as np
import requests
import io
import time
from datetime import date

# =========================== HELPERS / CACHES ==================================
@st.cache_data
def load_binance_trades_csv(file_or_path):
    """Lee CSV de trades con: id, price, qty, base_qty, time (ms), is_buyer_maker."""
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
    """Agrega trades → OHLCV + VWAP por 1T/1H/1D."""
    ohlc = trades_df["price"].resample(rule).agg(["first","max","min","last"])
    ohlc.columns = ["Open","High","Low","Close"]
    volume = trades_df["qty"].resample(rule).sum().rename("Volume")
    vwap = (trades_df["price"]*trades_df["qty"]).resample(rule).sum() / trades_df["qty"].resample(rule).sum()
    vwap = vwap.rename("VWAP")
    return pd.concat([ohlc, volume, vwap], axis=1).dropna(how="all")

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

# ---------------- Alpha Vantage (acciones) ROBUSTO ----------------
ALPHA_BASE = "https://www.alphavantage.co/query"

@st.cache_data(show_spinner=False)
def alpha_daily_adjusted_any(ticker: str, api_key: str, outputsize: str = "compact") -> pd.DataFrame:
    """
    TIME_SERIES_DAILY_ADJUSTED: intenta CSV y si no, JSON. Devuelve DataFrame
    con Date index y columnas: Open, High, Low, Close, Adj Close, Volume (si existen).
    """
    # ---- 1) Intento CSV
    params_csv = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": ticker,
        "apikey": api_key,
        "datatype": "csv",
        "outputsize": outputsize,  # 'compact' (≈100 días) o 'full'
    }
    r = requests.get(ALPHA_BASE, params=params_csv, timeout=25)
    r.raise_for_status()
    txt = r.text.lstrip()

    if not txt.startswith("{"):  # parece CSV válido
        try:
            df = pd.read_csv(io.StringIO(txt))
            df.rename(columns={
                "timestamp":"Date","open":"Open","high":"High","low":"Low",
                "close":"Close","adjusted_close":"Adj Close","volume":"Volume"
            }, inplace=True)
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df = df.dropna(subset=["Date"]).sort_values("Date").set_index("Date")
            return df
        except Exception:
            pass  # caemos a JSON

    # ---- 2) Fallback JSON (cuando Alpha manda mensaje de límite/nota/err)
    params_json = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": ticker,
        "apikey": api_key,
        "outputsize": outputsize,
    }
    rj = requests.get(ALPHA_BASE, params=params_json, timeout=25)
    rj.raise_for_status()
    js = rj.json()

    # Mensajes típicos
    msg = js.get("Note") or js.get("Information") or js.get("Error Message")
    if msg:
        raise RuntimeError(msg)

    series = js.get("Time Series (Daily)") or js.get("Time Series Daily")
    if not series:
        raise RuntimeError("Respuesta JSON no contiene series diarias")

    dfj = (
        pd.DataFrame.from_dict(series, orient="index")
          .rename(columns={
              "1. open":"Open","2. high":"High","3. low":"Low","4. close":"Close",
              "5. adjusted close":"Adj Close","6. volume":"Volume"
          })
    )
    dfj.index = pd.to_datetime(dfj.index, errors="coerce")
    for c in ["Open","High","Low","Close","Adj Close","Volume"]:
        if c in dfj.columns:
            dfj[c] = pd.to_numeric(dfj[c], errors="coerce")
    dfj = dfj.sort_index().dropna(how="all")
    dfj.index.name = "Date"
    return dfj

def alpha_fetch_window(ticker: str, api_key: str, start: date, end: date, outputsize="compact") -> pd.DataFrame:
    """
    Trae datos y recorta por fechas. Hace 2 reintentos con pequeño backoff
    para respetar ~5 req/min del plan free.
    """
    delays = [0, 12]  # segundos
    last = None
    for d in delays:
        if d: time.sleep(d)
        try:
            df = alpha_daily_adjusted_any(ticker, api_key, outputsize=outputsize)
            mask = (df.index.date >= start) & (df.index.date <= end)
            return df.loc[mask]
        except Exception as e:
            last = e
    raise last if last else RuntimeError("Fallo desconocido Alpha Vantage")

# =========================== NAV / RUTEO (ejemplo) ==============================
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

# ============================ PÁGINA / UI ======================================
if pagina == "📊 Exploración de Datos":
    st.title("📊 Exploración de Datos")

    # -------------------- 1) BITCOIN DESDE CSV (TRADES → VELAS) ----------------
    st.subheader("1) Bitcoin desde CSV (trades → velas)")
    st.caption("Sube tu CSV con columnas: id, price, qty, base_qty, time (ms), is_buyer_maker.")
    btc_trades_file = st.file_uploader("Sube CSV de trades (BTC/USDT, etc.)", type=["csv"], key="btc_trades")
    rule_label = st.selectbox("Intervalo de agregación", ["1T (1 minuto)","1H (1 hora)","1D (1 día)"], index=2)
    rule = {"1T (1 minuto)":"1T","1H (1 hora)":"1H","1D (1 día)":"1D"}[rule_label]
    price_to_plot = st.radio("Precio a graficar", ["Close","VWAP"], horizontal=True, index=0)

    if btc_trades_file is not None:
        try:
            trades_df = load_binance_trades_csv(btc_trades_file)
            st.success(f"Trades cargados: {len(trades_df):,} · {trades_df.index.min()} → {trades_df.index.max()}")
            with st.expander("Muestra de trades (primeras 20 filas)"):
                st.dataframe(trades_df.head(20), use_container_width=True)

            btc_ohlcv = trades_to_ohlcv(trades_df, rule=rule)
            st.write(f"### Velas BTC ({rule_label})")
            st.dataframe(btc_ohlcv.tail(20), use_container_width=True)
            st.line_chart(btc_ohlcv[[price_to_plot]].dropna(), height=280, use_container_width=True)

            with st.expander("Estadísticas rápidas (BTC)"):
                quick_stats(btc_ohlcv, price_col="Close")
            df_download_button(btc_ohlcv, f"btc_ohlcv_{rule}.csv", "📥 Descargar velas BTC (CSV)")
        except Exception as e:
            st.error(f"Error con el CSV de BTC: {e}")
    else:
        st.info("Sube el CSV para ver velas de BTC.")

    st.markdown("---")

    # -------------------- 2) ACCIONES (AMZN / ORCL) CON ALPHA VANTAGE ----------
    st.subheader("2) Acciones (AMZN / ORCL) desde Alpha Vantage (sin yfinance)")
    st.caption("Usa tu API key gratuita. En Cloud, guárdala en Secrets como ALPHAVANTAGE_API_KEY.")

    # API key: desde secrets o input rápido
    api_key = st.secrets.get("ALPHAVANTAGE_API_KEY", "")
    if not api_key:
        api_key = st.text_input("API Key de Alpha Vantage", type="password")

    c1, c2, c3 = st.columns(3)
    with c1:
        start_date = st.date_input("Desde", pd.to_datetime("2018-01-01").date(), key="av_start")
    with c2:
        end_date = st.date_input("Hasta", pd.Timestamp.today().date(), key="av_end")
    with c3:
        outputsize = st.selectbox("Tamaño", ["compact (≈100 días)","full (todo)"], index=0)
        outputsize = "compact" if outputsize.startswith("compact") else "full"

    for tk in ["AMZN", "ORCL"]:
        st.write(f"### {tk}")
        if not api_key:
            st.warning("Ingresa tu API key para descargar datos.")
            continue
        try:
            df_eq = alpha_fetch_window(tk, api_key, start_date, end_date, outputsize=outputsize)
            if df_eq.empty:
                st.warning("Sin datos en el rango indicado.")
                continue
            st.dataframe(df_eq.tail(20), use_container_width=True)
            price_col = "Adj Close" if "Adj Close" in df_eq.columns and df_eq["Adj Close"].notna().any() else "Close"
            st.line_chart(df_eq[[price_col]].dropna(), height=260, use_container_width=True)

            with st.expander(f"Estadísticas rápidas ({tk})"):
                quick_stats(df_eq, price_col)

            df_download_button(df_eq, f"{tk}_alpha_{start_date}_{end_date}.csv",
                               f"📥 Descargar {tk} (CSV)")
        except Exception as e:
            st.error(f"No pude traer {tk} desde Alpha Vantage: {e}")

    st.markdown("---")
    st.info("Tip: para portafolios usa **Adj Close** (acciones) y **Close/VWAP** (BTC) para retornos. "
            "Alpha Vantage free permite ~5 req/min; con AMZN y ORCL estás dentro del límite.")
