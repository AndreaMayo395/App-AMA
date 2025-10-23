# ───────────────────────────────────────────────────────────────────────────────
# PESTAÑA: 📊 Exploración de Datos  (BTC desde CSV; AMZN/ORCL vía Stooq robusto)
# Reqs: pip install streamlit pandas numpy requests
# ───────────────────────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import numpy as np
import requests
import io
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

# ---------------- Stooq robusto (sin API key) ---------------------------------
_STOOQ_ENDPOINTS = [
    "https://stooq.com/q/d/l/?s={code}&i=d",
    "https://stooq.pl/q/d/l/?s={code}&i=d",
    "http://stooq.com/q/d/l/?s={code}&i=d",   # fallback http
    "http://stooq.pl/q/d/l/?s={code}&i=d",
]
_STOOQ_HEADERS = {"User-Agent": "Mozilla/5.0 (StreamlitApp; +https://streamlit.io)"}

@st.cache_data(show_spinner=False)
def fetch_stooq_daily_robust(ticker_code: str) -> pd.DataFrame:
    """
    Intenta varios mirrors/HTTPs con headers. Devuelve DataFrame con
    Date index y columnas: Open, High, Low, Close, Volume.
    """
    errs = []
    for tpl in _STOOQ_ENDPOINTS:
        url = tpl.format(code=ticker_code.lower())
        try:
            r = requests.get(url, headers=_STOOQ_HEADERS, timeout=20)
            r.raise_for_status()
            txt = r.text.strip()
            # Stooq devuelve CSV con cabecera "Date,Open,High,Low,Close,Volume"
            if not txt or txt.startswith("<!DOCTYPE") or "Error 404" in txt:
                errs.append(f"HTML/ vacío en {url}")
                continue
            df = pd.read_csv(io.StringIO(txt))
            # Normalizar columnas (por si vienen capitalizadas distinto)
            df.rename(columns=str.title, inplace=True)  # Date, Open, High, Low, Close, Volume
            if "Date" not in df.columns:
                errs.append(f"Sin columna Date en {url}")
                continue
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df = df.dropna(subset=["Date"]).sort_values("Date").set_index("Date")
            # Asegurar tipos numéricos
            for c in ["Open","High","Low","Close","Volume"]:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors="coerce")
            df = df.dropna(how="all")
            if df.empty:
                errs.append(f"DataFrame vacío en {url}")
                continue
            return df
        except Exception as e:
            errs.append(f"{url} → {e}")
            continue
    raise RuntimeError("Stooq no respondió en ninguno de los mirrors. Detalles: " + " | ".join(errs))

# =========================== NAV / RUTEO (de ejemplo) ==========================
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

    # -------------------- 2) ACCIONES (AMZN / ORCL) SIN KEYS -------------------
    st.subheader("2) Acciones (AMZN / ORCL) sin API key (Stooq)")
    st.caption("Si la descarga web falla en tu Cloud, sube un CSV propio como fallback.")

    c1, c2 = st.columns(2)
    with c1:
        start_date = st.date_input("Desde", pd.to_datetime("2018-01-01").date(), key="stq_start")
    with c2:
        end_date = st.date_input("Hasta", pd.Timestamp.today().date(), key="stq_end")

    # Fallback: permitir subir CSV locales de AMZN/ORCL
    col_up1, col_up2 = st.columns(2)
    amzn_csv = col_up1.file_uploader("Opcional: subir AMZN (CSV)", type=["csv"], key="amzn_csv")
    orcl_csv = col_up2.file_uploader("Opcional: subir ORCL (CSV)", type=["csv"], key="orcl_csv")

    tickers = [("AMZN", "amzn.us", amzn_csv), ("ORCL", "orcl.us", orcl_csv)]
    for name, code, upfile in tickers:
        st.write(f"### {name}")
        try:
            if upfile is not None:
                # usar CSV subido
                df = pd.read_csv(upfile)
                df.rename(columns=str.title, inplace=True)
                if "Date" not in df.columns:
                    raise ValueError("El CSV debe tener columna 'Date'.")
                df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
                df = df.dropna(subset=["Date"]).sort_values("Date").set_index("Date")
            else:
                # traer de Stooq con mirrors/headers
                df = fetch_stooq_daily_robust(code)

            # filtro por fechas
            mask = (df.index.date >= start_date) & (df.index.date <= end_date)
            df_f = df.loc[mask].copy()
            if df_f.empty:
                st.warning("Sin datos en el rango elegido.")
                continue

            st.dataframe(df_f.tail(20), use_container_width=True)
            st.line_chart(df_f[["Close"]].dropna(), height=260, use_container_width=True)

            with st.expander(f"Estadísticas rápidas ({name})"):
                quick_stats(df_f, "Close")

            df_download_button(df_f, f"{name}_stooq_{start_date}_{end_date}.csv", f"📥 Descargar {name} (CSV)")
        except Exception as e:
            st.error(f"No pude traer {name}: {e}")

    st.markdown("---")
    st.info(
        "Notas: Stooq entrega OHLCV diarios EOD; si el servicio está bloqueado en tu entorno, "
        "sube tus CSV de AMZN/ORCL con columnas Date, Open, High, Low, Close, Volume. "
        "Para portafolios, usa **Close** (o **Adj Close** si tu CSV lo trae) y para BTC usa Close/VWAP."
    )
