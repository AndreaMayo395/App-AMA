import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ============================
# Configuración de la página
# ============================
st.set_page_config(
    page_title="Finanzas Personales 💰",
    page_icon="💸",
    layout="wide"
)

# ============================
# Encabezado
# ============================
st.title("💰 Panel de Finanzas Personales")
st.caption("Controla tus ingresos, gastos y metas de ahorro en un solo lugar.")

# ============================
# Cargar datos
# ============================
@st.cache_data
def cargar_datos():
    return pd.read_csv("data/ejemplo_finanzas.csv", parse_dates=["Fecha"])

data = cargar_datos()

# ============================
# Sidebar
# ============================
st.sidebar.header("⚙️ Configuración")
moneda = st.sidebar.selectbox("Moneda base", ["USD", "COP", "EUR", "MXN"])
mostrar_tabla = st.sidebar.checkbox("Mostrar tabla de datos", True)
st.sidebar.markdown("---")

# ============================
# Filtros
# ============================
st.sidebar.subheader("Filtros")
tipo_filtro = st.sidebar.multiselect(
    "Filtrar por tipo de movimiento:",
    options=data["Tipo"].unique(),
    default=data["Tipo"].unique()
)
data_filtrada = data[data["Tipo"].isin(tipo_filtro)]

# ============================
# Mostrar datos
# ============================
if mostrar_tabla:
    st.subheader("📊 Movimientos Financieros")
    st.dataframe(data_filtrada, use_container_width=True)

# ============================
# Gráficos
# ============================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Distribución por Categoría")
    fig1 = px.bar(
        data_filtrada,
        x="Categoría",
        y="Monto",
        color="Tipo",
        color_discrete_map={"Ingreso": "green", "Gasto": "red", "Ahorro": "blue"},
        title="Ingresos vs Gastos por Categoría"
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("🧩 Proporción de Ingresos y Gastos")
    fig2 = px.pie(
        data_filtrada,
        names="Tipo",
        values="Monto",
        title="Distribución del Flujo Financiero",
        hole=0.4
    )
    st.plotly_chart(fig2, use_container_width=True)

# ============================
# Metas
# ============================
st.subheader("🎯 Meta de Ahorro")
meta = st.slider("Define tu meta de ahorro mensual", 0, 2000, 1000, 100)
ahorro_actual = data[data["Tipo"] == "Ahorro"]["Monto"].sum()
porcentaje = round((ahorro_actual / meta) * 100, 1) if meta > 0 else 0

col1, col2 = st.columns(2)
col1.metric("Ahorro actual", f"{ahorro_actual} {moneda}", delta=f"{porcentaje}% de la meta")
col2.progress(min(porcentaje / 100, 1.0))

# ============================
# Reporte final
# ============================
total_ingresos = data[data["Tipo"] == "Ingreso"]["Monto"].sum()
total_gastos = -data[data["Tipo"] == "Gasto"]["Monto"].sum()
balance = total_ingresos - total_gastos

st.markdown("---")
st.subheader("📋 Resumen General")

c1, c2, c3 = st.columns(3)
c1.metric("Ingresos Totales", f"{total_ingresos} {moneda}")
c2.metric("Gastos Totales", f"{total_gastos} {moneda}")
c3.metric("Balance Neto", f"{balance} {moneda}", delta_color="normal")

st.markdown("---")
st.caption("© 2025 Finanzas Inteligentes | Desarrollado con ❤️ en Streamlit")
