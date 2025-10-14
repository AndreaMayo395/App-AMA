# ==========================================================
# 💰 Finanzas Personales - Streamlit App (solo Streamlit + Pandas)
# ==========================================================
import subprocess
import sys
import time

import streamlit as st

# ========== Instalación automática mínima ==========
def instalar_paquetes():
    with st.spinner("🔧 Instalando dependencias... por favor espera unos segundos"):
        subprocess.run([sys.executable, "-m", "pip", "install", "pandas"], stdout=subprocess.PIPE)
        time.sleep(1)

try:
    import pandas as pd
except ModuleNotFoundError:
    instalar_paquetes()
    import pandas as pd

# ============================
# CONFIGURACIÓN DE PÁGINA
# ============================
st.set_page_config(page_title="Finanzas Personales 💰", page_icon="💸", layout="wide")

# ============================
# ENCABEZADO
# ============================
st.title("💰 Panel de Finanzas Personales")
st.caption("Versión ultraliviana — sin librerías externas, rápida y sencilla.")

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
# TABLA
# ============================
if mostrar_tabla:
    st.subheader("📋 Movimientos Financieros")
    st.dataframe(data, use_container_width=True)

# ============================
# GRÁFICOS NATIVOS DE STREAMLIT
# ============================
st.subheader("📈 Ingresos y Gastos por Categoría")

# Creamos columnas separadas para ingresos y gastos
ingresos = data[data["Monto"] > 0][["Categoría", "Monto"]].set_index("Categoría")
gastos = data[data["Monto"] < 0][["Categoría", "Monto"]].set_index("Categoría").abs()

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Ingresos**")
    st.bar_chart(ingresos)

with col2:
    st.markdown("**Gastos**")
    st.bar_chart(gastos)

# ============================
# META DE AHORRO
# ============================
st.subheader("🎯 Meta de Ahorro")
meta = st.slider("Define tu meta de ahorro mensual", 0, 2000, 1000, 100)
ahorro_actual = data[data["Tipo"] == "Ahorro"]["Monto"].sum()
porcentaje = round((ahorro_actual / meta) * 100, 1) if meta > 0 else 0

col1, col2 = st.columns(2)
col1.metric("Ahorro actual", f"{ahorro_actual} {moneda}", delta=f"{porcentaje}% de la meta")
col2.progress(min(porcentaje / 100, 1.0))

# ============================
# RESUMEN GENERAL
# ============================
total_ingresos = data[data["Tipo"] == "Ingreso"]["Monto"].sum()
total_gastos = -data[data["Tipo"] == "Gasto"]["Monto"].sum()
balance = total_ingresos - total_gastos

st.markdown("---")
st.subheader("📊 Resumen General")

c1, c2, c3 = st.columns(3)
c1.metric("Ingresos Totales", f"{total_ingresos} {moneda}")
c2.metric("Gastos Totales", f"{total_gastos} {moneda}")
c3.metric("Balance Neto", f"{balance} {moneda}")

# ============================
# GRÁFICO DEL BALANCE
# ============================
st.subheader("📉 Evolución del Balance Mensual (Ejemplo)")

# Generamos datos ficticios para ilustrar
meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul"]
balance_mensual = pd.DataFrame({
    "Mes": meses,
    "Balance": [300, 450, 200, 700, 650, 900, 800]
}).set_index("Mes")

st.area_chart(balance_mensual)

# ============================
# PIE DE PÁGINA
# ============================
st.markdown("---")
st.caption("© 2025 Finanzas Inteligentes | Desarrollado con ❤️ y solo Streamlit 🚀")
