import streamlit as st

st.set_page_config(page_title="Análisis de Portafolio", page_icon="💹", layout="wide")

st.title("💹 Análisis de Portafolio de Inversión")
st.markdown("""
Bienvenido a la aplicación de análisis financiero.  
Esta herramienta permite **explorar, analizar y optimizar portafolios de inversión** de manera interactiva.

**Módulos disponibles:**
1. 📊 Exploración de Datos  
2. 📈 Análisis de Portafolio  
3. 💵 Rendimiento y Riesgo  
4. 🧮 Optimización de Portafolio  
5. 📉 Simulaciones Montecarlo
""")

st.info("Usa el menú lateral de Streamlit para navegar entre módulos.")
