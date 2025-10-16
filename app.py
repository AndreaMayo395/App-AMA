import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Análisis de Portafolio 💹", page_icon="💸", layout="wide")

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
        "💵 Rendimiento y Riesgo",
        "🧮 Optimización",
        "📉 Simulación Montecarlo"
    )
)

# =============================
# CONTENIDO DINÁMICO
# =============================
if pagina == "🏠 Inicio":
    st.title("💹 Análisis de Portafolio de Inversión")
    st.markdown("""
    Bienvenido a la app interactiva de **análisis financiero**.
    
    Usa el menú lateral 👈 para navegar entre los módulos:
    - **📊 Exploración de Datos**: carga y revisa tu dataset.
    - **📈 Análisis de Portafolio**: calcula rendimientos y correlaciones.
    - **💵 Rendimiento y Riesgo**: analiza el desempeño de tus activos.
    - **🧮 Optimización**: encuentra la mejor combinación de pesos.
    - **📉 Montecarlo**: simula escenarios futuros.
    """)

# --- Exploración de Datos ---
elif pagina == "📊 Exploración de Datos":
    st.title("📊 Exploración de Datos")
    archivo = st.file_uploader("Sube tu archivo CSV:", type=["csv"])
    if archivo:
        df = pd.read_csv(archivo)
        st.dataframe(df.head(), use_container_width=True)
        st.write(df.describe())
    else:
        st.info("Sube un archivo CSV para comenzar.")

# --- Análisis de Portafolio ---
elif pagina == "📈 Análisis de Portafolio":
    st.title("📈 Análisis de Portafolio")
    archivo = st.file_uploader("Sube datos de precios:", type=["csv"])
    if archivo:
        df = pd.read_csv(archivo, index_col=0, parse_dates=True)
        retornos = df.pct_change().dropna()
        st.line_chart(retornos)
        st.subheader("📊 Correlación entre activos")
        st.dataframe(retornos.corr())
    else:
        st.info("Sube un archivo CSV para ver los rendimientos.")

# --- Rendimiento y Riesgo ---
elif pagina == "💵 Rendimiento y Riesgo":
    st.title("💵 Rendimiento y Riesgo")
    archivo = st.file_uploader("Sube tus datos:", type=["csv"])
    if archivo:
        df = pd.read_csv(archivo, index_col=0)
        retornos = df.pct_change().dropna()
        rendimiento = retornos.mean() * 252
        riesgo = retornos.std() * np.sqrt(252)
        st.bar_chart(rendimiento)
        st.bar_chart(riesgo)
        st.dataframe(pd.DataFrame({"Rendimiento": rendimiento, "Riesgo": riesgo}))
    else:
        st.info("Sube un archivo CSV para continuar.")

# --- Optimización ---
elif pagina == "🧮 Optimización":
    st.title("🧮 Optimización de Portafolio")
    archivo = st.file_uploader("Sube precios históricos:", type=["csv"])
    if archivo:
        df = pd.read_csv(archivo, index_col=0)
        retornos = df.pct_change().dropna()
        rend = retornos.mean() * 252
        cov = retornos.cov() * 252
        n = len(df.columns)
        pesos = np.random.dirichlet(np.ones(n), 5000)
        port_rend = pesos.dot(rend)
        port_riesgo = np.sqrt(np.diag(pesos @ cov @ pesos.T))
        st.scatter_chart(pd.DataFrame({"Riesgo": port_riesgo, "Rendimiento": port_rend}))
    else:
        st.info("Sube un archivo CSV para simular portafolios.")

# --- Montecarlo ---
elif pagina == "📉 Simulación Montecarlo":
    st.title("📉 Simulación Montecarlo")
    r = st.number_input("Rendimiento esperado (%)", value=10.0) / 100
    sigma = st.number_input("Volatilidad (%)", value=15.0) / 100
    años = st.slider("Años", 1, 20, 10)
    simulaciones = 300
    st.subheader("🔮 Proyección de escenarios")
    np.random.seed(42)
    caminos = np.exp(np.cumsum((r - 0.5*sigma**2) + sigma * np.random.randn(años, simulaciones), axis=0))
    st.line_chart(caminos)
