import streamlit as st
import numpy as np
import pandas as pd

st.title("📉 Simulaciones Montecarlo")

st.markdown("""
Simula escenarios futuros de rendimiento de portafolio basados en tus parámetros de entrada.
""")

rendimiento_esperado = st.number_input("Rendimiento esperado anual (%)", value=10.0) / 100
volatilidad = st.number_input("Volatilidad anual (%)", value=15.0) / 100
años = st.slider("Número de años", 1, 20, 10)
simulaciones = 500

st.subheader("🔮 Simulaciones")
np.random.seed(42)
paths = np.exp(np.cumsum((rendimiento_esperado - 0.5 * volatilidad**2) * np.ones((años, simulaciones))
                         + volatilidad * np.random.randn(años, simulaciones), axis=0))
st.line_chart(paths)
