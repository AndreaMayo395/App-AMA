import streamlit as st
import pandas as pd
import numpy as np

st.title("💵 Rendimiento y Riesgo")

uploaded = st.file_uploader("Sube tus datos de precios:", type=["csv"])
if uploaded:
    df = pd.read_csv(uploaded, index_col=0)
    returns = df.pct_change().dropna()

    rendimiento = returns.mean() * 252
    riesgo = returns.std() * np.sqrt(252)

    st.subheader("📈 Rendimiento Anualizado")
    st.bar_chart(rendimiento)

    st.subheader("⚠️ Riesgo (Desviación estándar anualizada)")
    st.bar_chart(riesgo)

    st.dataframe(pd.DataFrame({"Rendimiento": rendimiento, "Riesgo": riesgo}))
else:
    st.info("Carga un archivo CSV para continuar.")
