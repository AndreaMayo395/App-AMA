import streamlit as st
import sys
import subprocess  # <- ¡este faltaba!

def ensure_pkg(pkg: str, spec: str | None = None) -> bool:
    """Intenta importar; si falla, instala con pip y vuelve a importar."""
    try:
        __import__(pkg)
        return True
    except Exception:
        pass
    try:
        with st.spinner(f"Instalando {pkg}..."):
            cmd = [sys.executable, "-m", "pip", "install", (spec or pkg), "--quiet"]
            subprocess.check_call(cmd)
        __import__(pkg)  # re-import tras instalar
        st.toast(f"{pkg} instalado ✅", icon="✅")
        return True
    except Exception as e:
        st.error(f"No pude instalar {pkg} automáticamente: {e}")
        return False

# yfinance on-demand
YF_AVAILABLE = ensure_pkg("yfinance", "yfinance>=0.2.40")
if YF_AVAILABLE:
    import yfinance as yf
else:
    yf = None




def _check_pkg(name):
    spec = importlib.util.find_spec(name)
    return spec is not None

st.sidebar.subheader("🔧 Diagnóstico")
st.sidebar.write("Python:", sys.version)
st.sidebar.write("yfinance instalado:", _check_pkg("yfinance"))
if _check_pkg("yfinance"):
    import yfinance as yf
    st.sidebar.write("yfinance versión:", getattr(yf, "__version__", "desconocida"))
else:
    st.sidebar.error("No se encontró yfinance. Revisa requirements.txt en la **raíz** y el log de build.")



"""
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="Análisis de Portafolio 💹", page_icon="💸", layout="wide")



# ── HELPERS ────────────────────────────────────────────────────────────────────
@st.cache_data
def load_binance_trades_csv(file_or_path):
   
    df = pd.read_csv(file_or_path)
    cols_lower = {c: c.lower() for c in df.columns}
    df = df.rename(columns=cols_lower)

    needed = {"price","qty","time"}
    if not needed.issubset(set(df.columns)):
        raise ValueError("CSV de trades debe tener al menos: price, qty, time")

    # convertir tipos
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce")
    # 'base_qty' (a veces se llama quoteQty). Si no existe, la calculamos si puedes (price*qty):
    if "base_qty" in df.columns:
        df["base_qty"] = pd.to_numeric(df["base_qty"], errors="coerce")
    else:
        df["base_qty"] = df["price"] * df["qty"]

    # time en milisegundos → datetime (sin zona)
    df["time"] = pd.to_datetime(df["time"], unit="ms", errors="coerce").dt.tz_localize(None)
    df = df.dropna(subset=["time","price","qty"]).sort_values("time").set_index("time")

    # renombrar opcionalmente para consistencia
    df = df.rename(columns={
        "id": "trade_id",
        "is_buyer_maker": "isBuyerMaker"
    })
    return df

def trades_to_ohlcv(trades_df, rule="1D"):
    
    ohlc = trades_df["price"].resample(rule).agg(["first","max","min","last"])
    ohlc.columns = ["Open","High","Low","Close"]
    volume = trades_df["qty"].resample(rule).sum().rename("Volume")
    vwap = (trades_df["price"]*trades_df["qty"]).resample(rule).sum() / trades_df["qty"].resample(rule).sum()
    vwap = vwap.rename("VWAP")
    out = pd.concat([ohlc, volume, vwap], axis=1).dropna(how="all")
    return out

@st.cache_data
def fetch_yf(ticker, start=None, end=None, interval="1d"):
    data = yf.download(ticker, start=start, end=end, interval=interval, auto_adjust=False, progress=False)
    if data.empty:
        raise ValueError(f"Sin datos para {ticker}")
    return data

def render_summary(df, price_col="Adj Close"):
    col = price_col if price_col in df.columns else "Close"
    if col not in df.columns:  # para BTC OHLCV derivado
        col = "Close" if "Close" in df.columns else df.columns[0]
    ret = df[col].pct_change().dropna()
    st.metric("Observaciones", len(df))
    st.write(pd.DataFrame({
        "Retorno medio (diario)": [ret.mean()],
        "Volatilidad (diaria)": [ret.std()],
        "Retorno acumulado": [(df[col].iloc[-1]/df[col].iloc[0]-1) if len(df)>1 else np.nan]
    }).T.rename(columns={0:""}))



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

    # ===================== 1) BITCOIN DESDE CSV DE TRADES ======================
    st.subheader("Bitcoin desde CSV (trades → velas)")
    st.caption("Sube tu CSV con columnas como: id, price, qty, base_qty, time, is_buyer_maker (tiempo en ms).")

    btc_trades_file = st.file_uploader("Sube CSV de trades (BTC/USDT, etc.)", type=["csv"], key="btc_trades")
    rule = st.selectbox("Intervalo de agregación", ["1T (1 minuto)","1H (1 hora)","1D (1 día)"], index=2)
    rule_map = {"1T (1 minuto)":"1T", "1H (1 hora)":"1H", "1D (1 día)":"1D"}

    if btc_trades_file is not None:
        try:
            trades_df = load_binance_trades_csv(btc_trades_file)
            st.success(f"Trades cargados: {len(trades_df):,} filas · rango: {trades_df.index.min().date()} → {trades_df.index.max().date()}")
            with st.expander("Ver muestra de trades (primeras 20 filas)"):
                st.dataframe(trades_df.head(20))

            btc_ohlcv = trades_to_ohlcv(trades_df, rule=rule_map[rule])
            st.write(f"### Velas BTC ({rule})")
            st.dataframe(btc_ohlcv.tail(20))
            st.line_chart(btc_ohlcv[["Close"]].dropna(), height=280)
            with st.expander("Estadísticas rápidas (BTC)"):
                render_summary(btc_ohlcv, price_col="Close")
        except Exception as e:
            st.error(f"Error con el CSV de BTC: {e}")
    else:
        st.info("Sube el CSV para ver precio y velas de BTC.")

    st.markdown("---")

    # ===================== 2) ACCIONES (AMZN / ORCL) ===========================
    st.subheader("Acciones con yfinance (AMZN / ORCL)")
    col1, col2, col3 = st.columns(3)
    with col1:
        start_date = st.date_input("Desde", pd.to_datetime("2018-01-01").date())
    with col2:
        end_date = st.date_input("Hasta", pd.Timestamp.today().date())
    with col3:
        interval = st.selectbox("Intervalo", ["1d","1wk","1mo"], index=0)

    for tk in ["AMZN", "ORCL"]:
        st.write(f"### {tk}")
        try:
            df = fetch_yf(tk, start=pd.to_datetime(start_date), end=pd.to_datetime(end_date), interval=interval)
            st.dataframe(df.tail(20))
            price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
            st.line_chart(df[[price_col]].dropna(), height=260)
            with st.expander(f"Estadísticas rápidas ({tk})"):
                render_summary(df, price_col)
        except Exception as e:
            st.error(f"No se pudo descargar {tk}: {e}")

    st.markdown("---")
    st.info("Nota: en trades de Binance, `qty` es volumen en el activo base; `base_qty` suele ser el valor en la moneda cotizada. Las velas usan OHLC del precio y `Volume = Σ qty`.")



elif pagina == "📈 Análisis de Portafolio":
    st.title("📈 Análisis de Portafolio")
    
elif pagina == "💵 Perfil de Riesgo":
    st.title("💵 Perfil de Riesgo")
    
elif pagina == "🧮 Estrategia":
    st.title("🧮 Ajustar la estrategia de Inversión")

    """

