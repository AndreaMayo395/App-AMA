import streamlit as st
import pandas as pd

st.title("📊 Exploración de Datos")

uploaded = st.file_uploader("Sube tu archivo CSV de portafolio:", type=["csv"])
if uploaded:
    df = pd.read_csv(uploaded)
    st.success("Datos cargados correctamente ✅")
    st.dataframe(df.head(), use_container_width=True)

    st.subheader("📈 Estadísticas básicas")
    st.write(df.describe())

    st.bar_chart(df.select_dtypes(include=["float", "int"]))
else:
    st.warning("Por favor, carga un archivo CSV para comenzar.")