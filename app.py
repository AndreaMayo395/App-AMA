# ==========================================================
# 💰 Finanzas Personales - Streamlit App
# Con instalación automática de dependencias 💻
# ==========================================================
import subprocess
import sys
import time

import streamlit as st

# ========== INSTALACIÓN AUTOMÁTICA =============
# Intenta importar, si falla instala los paquetes
def instalar_paquetes():
    with st.spinner("🔧 Instalando dependencias... por favor espera unos segundos"):
        for package in ["pandas", "plotly"]:
            subprocess.run([sys.executable, "-m", "pip", "install", package], stdout=subprocess.PIPE)
        time.sleep(1)  # pequeña pausa visual

try:
    import pandas as pd
    import plotly.express as px
except ModuleNotFoundError:
    instalar_paquetes()
    import pandas as pd
    import plotly.express as px

# ============================
# CONFIGURACIÓN DE PÁGINA
# ============================
st.set_page_config(page_title="Finanzas Personales 💰", page_icon="💸", layout="wide")

# ============================
# ENCABEZADO
# ============================
st.title("💰 Panel de Finanzas Personales")
st.caption("Controla tus ingresos, gastos y metas de ahorro de forma visual e interactiva.")

# ============================
# DATOS DE EJEMPLO
# ============================
data = pd.DataFrame({
    "Categoría": ["Salario", "Freelance", "Renta", "Comida", "Transporte", "Entretenimiento", "Ahorro"],
    "Monto": [2500, 800, 300, -600, -150, -200, 400],
    "Tipo": ["Ingreso", "Ingreso", "Ingreso", "Gasto", "Gasto", "Gasto", "Ahorro"]
})

# ============================
# SIDEBAR
# ============================
st.sidebar.header("⚙️ Configuración")
moneda = st.sidebar.selectbox("Moneda base", ["USD", "COP", "EUR", "MXN"])
mostrar_tabla = st.sidebar.checkbox("Mostrar tabla de datos", True)
st.sidebar.markdown("---")

# ============================
# TABLA DE DATOS
# ============================
if mostrar_tabla:
    st.subheader("📊 Movimientos Financieros")
    st.dataframe(data, use_container_width=True)

# ============================
# GRÁFICOS
# ============================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Distribución por Categoría")
    fig1 = px.bar(
        data,
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
        data,
        names="Tipo",
        values="Monto",
        title="Distribución del Flujo Financiero",
        hole=0.4
    )
    st.plotly_chart(fig2, use_container_width=True)

# ============================
# METAS DE AHORRO
# ============================
st.subheader("🎯 Meta de Ahorro")
meta = st.slider("Define tu meta de ahorro mensual", 0, 2000, 1000, 100)
ahorro_actual = data[data["Tipo"] == "Ahorro"]["Monto"].sum()
porcentaje = round((ahorro_actual / meta) * 100, 1) if meta > 0 else 0

col1, col2 = st.columns(2)
col1.metric("Ahorro actual", f"{ahorro_actual} {moneda}", delta=f"{porcentaje}% de la meta")
col2.progress(min(porcentaje / 100, 1.0))

# ============================
# REPORTE GENERAL
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
