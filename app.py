# ==========================================================
# 💰 Finanzas Personales - Streamlit App (sin Plotly)
# ==========================================================
import subprocess
import sys
import time

import streamlit as st

# ========= Instalación automática mínima ==========
def instalar_paquetes():
    with st.spinner("🔧 Instalando dependencias... por favor espera unos segundos"):
        for package in ["pandas", "matplotlib"]:
            subprocess.run([sys.executable, "-m", "pip", "install", package], stdout=subprocess.PIPE)
        time.sleep(1)

try:
    import pandas as pd
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    instalar_paquetes()
    import pandas as pd
    import matplotlib.pyplot as plt


# ============================
# CONFIGURACIÓN
# ============================
st.set_page_config(page_title="Finanzas Personales 💰", page_icon="💸", layout="wide")

st.title("💰 Panel de Finanzas Personales")
st.caption("Visualiza tus ingresos, gastos y metas de ahorro fácilmente — sin dependencias pesadas.")

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
    st.subheader("📊 Movimientos Financieros")
    st.dataframe(data, use_container_width=True)

# ============================
# GRÁFICO DE BARRAS
# ============================
st.subheader("📈 Ingresos y Gastos por Categoría")
# Crear gráfico con Matplotlib
fig, ax = plt.subplots()
colors = data["Tipo"].map({"Ingreso": "green", "Gasto": "red", "Ahorro": "blue"})
ax.bar(data["Categoría"], data["Monto"], color=colors)
ax.axhline(0, color="black", linewidth=0.8)
ax.set_ylabel(f"Monto ({moneda})")
ax.set_xlabel("Categoría")
ax.set_title("Ingresos vs Gastos por Categoría")
st.pyplot(fig)

# ============================
# GRÁFICO DE COMPOSICIÓN (pie)
# ============================
st.subheader("🧩 Proporción de Tipos de Movimiento")
tipo_totales = data.groupby("Tipo")["Monto"].sum().abs()
fig2, ax2 = plt.subplots()
ax2.pie(tipo_totales, labels=tipo_totales.index, autopct="%1.1f%%", colors=["green", "red", "blue"])
ax2.set_title("Distribución de Ingresos, Gastos y Ahorro")
st.pyplot(fig2)

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
# RESUMEN
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
st.caption("© 2025 Finanzas Inteligentes | Desarrollado con ❤️ sin Plotly 😎")
