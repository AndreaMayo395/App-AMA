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
        "Peso": [],           # Porcentaje o proporción del portafolio
        "Rendimiento": [],    # Rendimiento histórico o proyectado
        "Riesgo": []          # Volatilidad o riesgo asociado
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

elif pagina == "📈 Análisis de Portafolio":
    st.title("📈 Análisis de Portafolio")
    
elif pagina == "💵 Perfil de Riesgo":
    st.title("💵 Perfil de Riesgo")
    
elif pagina == "🧮 Estrategia":
    st.title("🧮 Ajustar la estrategia de Inversión")

    

