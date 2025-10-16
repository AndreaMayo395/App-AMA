import numpy as np
import pandas as pd

def calcular_retorno_log(df):
    return np.log(df / df.shift(1)).dropna()

def rendimiento_y_riesgo(df):
    returns = df.pct_change().dropna()
    return returns.mean() * 252, returns.std() * np.sqrt(252)