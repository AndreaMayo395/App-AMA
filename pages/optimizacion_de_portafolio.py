import streamlit as st
import pandas as pd
import numpy as np

st.title("🧮 Optimización del Portafolio")

uploaded = st.file_uploader("Sube el archivo de precios:", type=["csv"])
if uploaded:
    df = pd.read_csv(uploaded, index_col=0)
    returns = df.pct_change().dropna()

    rendimiento = returns.mean() * 252
    cov = returns.cov() * 252

    n = len(returns.columns)
    pesos = np.random.dirichlet(np.ones(n), 1000)

    rendimientos = pesos.dot(rendimiento)
    riesgos = np.sqrt(np.diag(pesos @ cov @ pesos.T))

    resultados = pd.DataFrame({"Rendimiento": rendimientos, "Riesgo": riesgos})
    st.scatter_chart(resultados, x="Riesgo", y="Rendimiento")
else:
    st.info("Sube tus datos de precios para calcular portafolios simulados.")
