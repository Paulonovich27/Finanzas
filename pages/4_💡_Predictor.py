# pages/4_💡_Predictor.py
import streamlit as st
import pandas as pd
from database import cargar_movimientos

st.set_page_config(page_title="Predictor de Excedentes", page_icon="💡", layout="wide")

st.subheader("💡 Asistente Predictivo")
st.info("Calcula qué hacer con el saldo libre de tus periodos registrados.")

df_movs = cargar_movimientos()

if not df_movs.empty:
    periodos_disponibles = sorted(df_movs['periodo'].dropna().unique().tolist(), reverse=True)
    mes_seleccionado = st.selectbox("Evaluar periodo:", periodos_disponibles)
    df_filtrado = df_movs[df_movs['periodo'] == mes_seleccionado]
    
    ingresos = df_filtrado[df_filtrado['tipo'] == 'Ingreso']['monto'].sum()
    gastos = df_filtrado[df_filtrado['tipo'] == 'Gasto']['monto'].sum()
    ahorros = df_filtrado[df_filtrado['tipo'] == 'Ahorro']['monto'].sum()
    saldo_disponible = ingresos - gastos - ahorros
    
    st.metric(f"Excedente proyectado", f"S/ {saldo_disponible:.2f}")
    if saldo_disponible > 800.0:
        st.success("✅ Excedente superior a S/ 800.")
    elif saldo_disponible > 0:
        st.warning(f"⚠️ Prioriza tu liquidez. Guárdalo como fondo de emergencia.")
    else:
        st.info("No cuentas con liquidez excedente en este periodo.")
else:
    st.info("Aún no tienes movimientos para evaluar.")