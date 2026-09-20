# pages/3_📥_Carga_Masiva.py
import streamlit as st
import pandas as pd
import re
from datetime import datetime
from config import CATEGORIAS_GASTOS, CATEGORIAS_INGRESOS_BASE, CATEGORIAS_AHORRO, obtener_periodo
from database import conectar_bd

st.set_page_config(page_title="Carga Masiva", page_icon="📥", layout="wide")

st.subheader("📥 Carga Rápida Inteligente (BCP)")
st.markdown("Copia y pega las líneas de tu estado de cuenta del BCP.")

texto_pegado = st.text_area("Pega los movimientos de tu PDF aquí:", height=250)

if st.button("🔍 Leer y Procesar Texto", type="primary"):
    if texto_pegado:
        lineas = texto_pegado.split('\n')
        movs_extraidos = []
        meses_bcp = {"ENE": "01", "FEB": "02", "MAR": "03", "ABR": "04", "MAY": "05", "JUN": "06",
                     "JUL": "07", "AGO": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DIC": "12"}
        
        for linea in lineas:
            linea = linea.strip()
            if not linea or "SALDO ANTERIOR" in linea: continue
            
            match = re.search(r'^(\d{2})([a-zA-Z]{3})\s+\d{2}[a-zA-Z]{3}\s+(.*?)\s+([\d\.,]+)\s*$', linea)
            
            if match:
                dia = match.group(1)
                mes_texto = match.group(2).upper()
                desc_raw = match.group(3).strip()
                monto = float(match.group(4).replace(',', ''))
                
                if monto == 0: continue
                
                desc = re.sub(r'\s+[\*1]\s*$', '', desc_raw).strip()
                desc_upper = desc.upper()
                
                tipo = "Gasto"
                categoria = "Otros Gastos" 
                
                if "YAPE DE" in desc_upper or "TRANSF.BCO" in desc_upper or "ABON" in desc_upper:
                    tipo, categoria = "Ingreso", "Otros Ingresos"
                elif "YAPE A" in desc_upper: categoria = "Prestamo Yape"
                elif "ECONOMAX" in desc_upper or "MALL" in desc_upper or "TAI LOY" in desc_upper: categoria = "Supermercado"
                elif "KURO KUMA" in desc_upper or "OXXO" in desc_upper: categoria = "Comida"
                elif "NETFLIX" in desc_upper or "YOUTUBE" in desc_upper or "CRUNCHYROLL" in desc_upper: categoria = "Internet"
                elif "CLAR0" in desc_upper or "TELE0" in desc_upper: categoria = "Celular Paul"
                elif "CALI0" in desc_upper: categoria = "Gas Pa"
                elif "PLUZ" in desc_upper: categoria = "Luz"
                elif "IMPUEST" in desc_upper: categoria = "Otros Gastos"
                elif "WARDA" in desc_upper: tipo, categoria = "Ahorro", "Fondo de Emergencia"
                    
                mes_num = meses_bcp.get(mes_texto, "01")
                fecha_str = f"2026-{mes_num}-{dia}"
                
                movs_extraidos.append({"fecha": fecha_str, "tipo": tipo, "categoria": categoria, "descripcion": desc, "monto": monto})
        
        if movs_extraidos:
            st.session_state['staging_data'] = pd.DataFrame(movs_extraidos)
            st.success(f"✅ Se clasificaron {len(movs_extraidos)} movimientos automáticamente.")
        else:
            st.error("No se detectó ningún movimiento. Verifica el formato.")

st.divider()

if 'staging_data' in st.session_state and not st.session_state['staging_data'].empty:
    st.markdown("### ✍️ Vista Previa y Edición")
    df_editado = st.data_editor(
        st.session_state['staging_data'], 
        use_container_width=True,
        column_config={
            "tipo": st.column_config.SelectboxColumn("Tipo", options=["Gasto", "Ingreso", "Ahorro"], required=True),
            "categoria": st.column_config.SelectboxColumn("Categoría", options=CATEGORIAS_GASTOS + CATEGORIAS_INGRESOS_BASE + CATEGORIAS_AHORRO, required=True),
            "monto": st.column_config.NumberColumn("Monto", format="S/ %.2f", min_value=0.0)
        }
    )
    
    c_bot1, c_bot2 = st.columns([1, 4])
    if c_bot1.button("💾 Guardar Todo en Neon", type="primary"):
        conn = conectar_bd()
        cur = conn.cursor()
        for _, row_fin in df_editado.iterrows():
            p_calc = obtener_periodo(str(row_fin['fecha'])[:10])
            cur.execute("INSERT INTO movimientos (tipo, categoria, monto, fecha, periodo, descripcion) VALUES (%s, %s, %s, %s, %s, %s)",
                        (row_fin['tipo'], row_fin['categoria'], row_fin['monto'], str(row_fin['fecha'])[:10], p_calc, row_fin['descripcion']))
        conn.commit()
        cur.close()
        conn.close()
        
        st.session_state['staging_data'] = pd.DataFrame() 
        st.success(f"¡{len(df_editado)} movimientos cargados!")
        st.rerun()
        
    if c_bot2.button("❌ Cancelar Carga"):
        st.session_state['staging_data'] = pd.DataFrame() 
        st.rerun()