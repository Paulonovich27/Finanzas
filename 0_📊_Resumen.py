# app.py
import streamlit as st
import pandas as pd
from datetime import datetime
from config import CATEGORIAS_GASTOS, obtener_periodo
from database import inicializar_tablas, cargar_movimientos

# Debe ser el primer comando de Streamlit
st.set_page_config(page_title="Mi Gestor Financiero", page_icon="💰", layout="wide")

# Inicializamos tablas por si es la primera vez
inicializar_tablas()

st.title("📊 Mi Gestor Financiero Familiar")
st.sidebar.success("👆 Selecciona un módulo en el menú superior.")

st.subheader("Visión General de tus Finanzas")

df_movs = cargar_movimientos()
periodo_actual_calc = obtener_periodo(datetime.now().strftime("%Y-%m-%d"))

if not df_movs.empty:
    periodos_disponibles = sorted(df_movs['periodo'].dropna().unique().tolist(), reverse=True)
    if periodo_actual_calc not in periodos_disponibles:
        periodos_disponibles.insert(0, periodo_actual_calc)
    indice_actual = periodos_disponibles.index(periodo_actual_calc) if periodo_actual_calc in periodos_disponibles else 0
    mes_seleccionado = st.selectbox("📅 Selecciona el Periodo", ["Todos los meses"] + periodos_disponibles, index=indice_actual + 1)
    
    df_filtrado = df_movs[df_movs['periodo'] == mes_seleccionado] if mes_seleccionado != "Todos los meses" else df_movs
else:
    mes_seleccionado = "Todos los meses"
    df_filtrado = pd.DataFrame()

if not df_filtrado.empty:
    ingresos = df_filtrado[df_filtrado['tipo'] == 'Ingreso']['monto'].sum()
    gastos = df_filtrado[df_filtrado['tipo'] == 'Gasto']['monto'].sum()
    ahorros = df_filtrado[df_filtrado['tipo'] == 'Ahorro']['monto'].sum()
    saldo = ingresos - gastos - ahorros
    
    st.markdown(f"""
    <div style="display: flex; gap: 15px; margin-bottom: 25px; flex-wrap: wrap;">
        <div style="flex: 1; padding: 20px; border-radius: 10px; background-color: #e6f4ea; border: 1px solid #ceead6; text-align: center;">
            <h4 style="margin: 0; color: #137333;">Ingresos</h4>
            <h2 style="margin: 5px 0 0 0; color: #0d652d;">S/ {ingresos:.2f}</h2>
        </div>
        <div style="flex: 1; padding: 20px; border-radius: 10px; background-color: #fce8e6; border: 1px solid #fad2cf; text-align: center;">
            <h4 style="margin: 0; color: #c5221f;">Gastos</h4>
            <h2 style="margin: 5px 0 0 0; color: #a50e0e;">S/ {gastos:.2f}</h2>
        </div>
        <div style="flex: 1; padding: 20px; border-radius: 10px; background-color: #e8f0fe; border: 1px solid #d2e3fc; text-align: center;">
            <h4 style="margin: 0; color: #1967d2;">Ahorros</h4>
            <h2 style="margin: 5px 0 0 0; color: #174ea6;">S/ {ahorros:.2f}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.metric("Saldo Libre / Excedente", f"S/ {saldo:.2f}")
    st.divider()
    
    st.subheader("💡 Diagnóstico Inteligente (Smart Insights)")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        gasto_comida = df_filtrado[(df_filtrado['tipo'] == 'Gasto') & (df_filtrado['categoria'].isin(['Comida', 'Supermercado', 'Mercado']))]['monto'].sum()
        if gasto_comida == 0:
            st.warning("⚠️ **Falsa Liquidez:** Cero gastos registrados en alimentación.")
        else:
            st.success(f"✅ **Alimentación al día:** Llevas S/ {gasto_comida:.2f}")
        if saldo > 1000:
            st.success(f"✅ **Buen Flujo:** Tienes excedente saludable.")
        elif saldo < 0:
            st.error(f"🚨 **Déficit:** S/ {abs(saldo):.2f} en contra.")
    with col_s2:
        yapes_peq = df_filtrado[(df_filtrado['categoria'] == 'Prestamo Yape') | ((df_filtrado['tipo'] == 'Gasto') & (df_filtrado['monto'] < 30))]['monto'].sum()
        if yapes_peq > 300:
            st.error(f"🐜 **Gastos Hormiga:** S/ {yapes_peq:.2f} acumulados.")
        else:
            st.info(f"🔍 **Microgastos Controlados:** S/ {yapes_peq:.2f}")
        
    st.divider()
    
    st.markdown("### 📋 Listado de Movimientos")
    columnas_mostrar = ['fecha', 'periodo', 'tipo', 'categoria', 'descripcion', 'monto']
    df_estilizado = df_filtrado[columnas_mostrar].style.set_properties(**{'text-align': 'center'})
    st.dataframe(df_estilizado, use_container_width=True, hide_index=True)
    
else:
    st.info("No hay movimientos registrados para este periodo.")

st.divider()
st.markdown("### 🧾 Cuadre por Archivo de Origen")
st.markdown("Audita la cantidad de movimientos y los montos totales para cuadrar con tus PDFs originales.")

if not df_filtrado.empty and 'origen' in df_filtrado.columns:
    # 1. Agrupar para contar la cantidad de datos y sumar los montos
    df_agrupado = df_filtrado.groupby(['origen', 'tipo']).agg(
        cantidad=('monto', 'count'),
        total_monto=('monto', 'sum')
    ).unstack(fill_value=0)
    
    # 2. Aplanar y organizar las columnas
    df_agrupado.columns = ['_'.join(col).strip() for col in df_agrupado.columns.values]
    df_agrupado = df_agrupado.reset_index()

    # 3. Construir la tabla limpia
    df_cuadre = pd.DataFrame()
    df_cuadre['origen'] = df_agrupado['origen']
    
    # Manejar los datos por si algún PDF no tiene ingresos o no tiene gastos
    ingresos_cant = df_agrupado['cantidad_Ingreso'] if 'cantidad_Ingreso' in df_agrupado.columns else 0
    gastos_cant = df_agrupado['cantidad_Gasto'] if 'cantidad_Gasto' in df_agrupado.columns else 0
    
    df_cuadre['Movimientos'] = ingresos_cant + gastos_cant
    df_cuadre['Ingresos'] = df_agrupado['total_monto_Ingreso'] if 'total_monto_Ingreso' in df_agrupado.columns else 0.0
    df_cuadre['Gastos'] = df_agrupado['total_monto_Gasto'] if 'total_monto_Gasto' in df_agrupado.columns else 0.0
    
    # 4. CREAR LA FILA DE TOTALES AL FONDO
    fila_total = pd.DataFrame({
        'origen': ['TOTAL GENERAL'],
        'Movimientos': [df_cuadre['Movimientos'].sum()],
        'Ingresos': [df_cuadre['Ingresos'].sum()],
        'Gastos': [df_cuadre['Gastos'].sum()]
    })
    
    df_cuadre = pd.concat([df_cuadre, fila_total], ignore_index=True)
    
    # 5. Mostrar la tabla con un diseño compacto
    st.dataframe(
        df_cuadre,
        use_container_width=True,
        hide_index=True,
        column_config={
            "origen": st.column_config.TextColumn("Archivo / Origen de Datos"),
            "Movimientos": st.column_config.NumberColumn("N° de Movimientos"),
            "Ingresos": st.column_config.NumberColumn("Total Ingresos (Abonos)", format="S/ %.2f"),
            "Gastos": st.column_config.NumberColumn("Total Gastos (Cargos)", format="S/ %.2f")
        }
    )
else:
    st.info("No hay datos suficientes en este periodo para realizar el cuadre.")