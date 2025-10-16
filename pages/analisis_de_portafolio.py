import streamlit as st
import pandas as pd

st.title("📈 Análisis de Portafolio")

st.markdown("""
Este módulo calcula el **rendimiento diario y acumulado** de los activos en tu portafolio.
""")

uploaded = st.file_uploader("Carga el mismo archivo de precios:", type=["csv"])
if uploaded:
    df = pd.read_csv(uploaded, index_col=0, parse_dates=True)
    returns = df.pct_change().dropna()
    st.line_chart(returns)
    st.subheader("📊 Correlación entre activos")
    st.dataframe(returns.corr())
else:
    st.info("Sube un archivo CSV para analizar los rendimientos.")
