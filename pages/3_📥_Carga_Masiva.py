# pages/3_📥_Carga_Masiva.py
import streamlit as st
import pandas as pd
import re
import time
from datetime import datetime
from config import CATEGORIAS_GASTOS, CATEGORIAS_INGRESOS_BASE, CATEGORIAS_AHORRO, obtener_periodo
from database import conectar_bd
import pdfplumber

# IMPORTAMOS EL MOTOR SEPARADO
from motor_reglas import aplicar_reglas

st.set_page_config(page_title="Carga Masiva", page_icon="📥", layout="wide")
st.subheader("📥 Carga Rápida Inteligente")

banco_seleccionado = st.radio("🏦 Selecciona el Banco:", ["BCP (Texto)", "Banbif (Lector de PDF)", "BBVA (Lector de PDF)"], horizontal=True)
movs_extraidos = []

# ==========================================
# LECTURA DE BANCOS
# ==========================================
if banco_seleccionado == "BCP (Texto)":
    texto_pegado = st.text_area("📝 Pega los movimientos de BCP aquí:", height=200)
    if st.button("🔍 Extraer", type="primary") and texto_pegado:
        meses_bcp = {"ENE": "01", "FEB": "02", "MAR": "03", "ABR": "04", "MAY": "05", "JUN": "06", "JUL": "07", "AGO": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DIC": "12"}
        for linea_raw in texto_pegado.split('\n'):
            linea = linea_raw.rstrip('\r') # Evitamos caracteres invisibles raros
            
            # Expresión regular que captura el texto y respeta los espacios al final
            match = re.search(r'^(\d{2})([a-zA-Z]{3})\s+\d{2}[a-zA-Z]{3}\s+(.*?)\s+([\d\.,]+)(\s*)$', linea)
            if match:
                dia, mes_texto, desc_raw, monto_str, espacios_finales = match.groups()
                monto = float(monto_str.replace(',', ''))
                if monto == 0: continue
                
                desc_raw = re.sub(r'\s+[\*1]\s*$', '', desc_raw).strip()
                
                # 🌟 MAGIA ESPACIAL: Determinamos si es Ingreso o Gasto por su posición visual
                if len(espacios_finales) > 5:
                    tipo_ini = "Gasto"
                else:
                    tipo_ini = "Ingreso"
                    
                # Refuerzo por si acaso el texto copiado perdió el formato
                if "YAPE DE" in desc_raw.upper() or "DEPOSITO" in desc_raw.upper():
                    tipo_ini = "Ingreso"
                    
                # Pasamos los datos por el motor
                tipo, cat, desc = aplicar_reglas(desc_raw, monto, tipo_ini)
                fecha_str = f"2026-{meses_bcp.get(mes_texto.upper(), '01')}-{dia}"
                
                movs_extraidos.append({
                    "fecha": fecha_str, 
                    "tipo": tipo, 
                    "categoria": cat, 
                    "descripcion": desc, 
                    "monto": monto, 
                    "origen": "Texto BCP"
                })
                
elif banco_seleccionado == "Banbif (Lector de PDF)":
    archivos_pdf = st.file_uploader("📄 Sube PDFs de Banbif", type=["pdf"], accept_multiple_files=True)
    if st.button("🔍 Extraer", type="primary") and archivos_pdf:
        with st.spinner("Procesando PDFs..."):
            for archivo in archivos_pdf:
                with pdfplumber.open(archivo) as pdf:
                    for pagina in pdf.pages:
                        if texto := pagina.extract_text():
                            for linea in texto.split('\n'):
                                match = re.search(r'^(\d{2}/\d{2}/\d{4})\s+(.*?)\s+([+-]?\s*[\d,]+\.\d{2})\s*$', linea.strip())
                                if match:
                                    f_raw, d_raw, m_str = match.groups()
                                    monto = float(m_str.replace(',', '').replace(' ', ''))
                                    if monto == 0: continue
                                    tipo, cat, desc = aplicar_reglas(d_raw.strip(), abs(monto), "Ingreso" if monto > 0 else "Gasto")
                                    fecha_str = datetime.strptime(f_raw, "%d/%m/%Y").strftime("%Y-%m-%d")
                                    movs_extraidos.append({"fecha": fecha_str, "tipo": tipo, "categoria": cat, "descripcion": desc, "monto": abs(monto), "origen": archivo.name})

elif banco_seleccionado == "BBVA (Lector de PDF)":
    archivos_pdf = st.file_uploader("📄 Sube PDFs de BBVA", type=["pdf"], accept_multiple_files=True)
    if st.button("🔍 Extraer", type="primary") and archivos_pdf:
        with st.spinner("Procesando PDFs..."):
            for archivo in archivos_pdf:
                with pdfplumber.open(archivo) as pdf:
                    for pagina in pdf.pages:
                        if texto := pagina.extract_text():
                            for linea in texto.split('\n'):
                                match = re.search(r'^(\d{2}-\d{2})\s+\d{2}-\d{2}\s+(.*?)\s+(?:VEN|BMV|BTE|.*?)\s+\d+\s+([\d,]+\.\d{2}-?)\s*(?:[\d,]+\.\d{2})?\s*$', linea.strip())
                                if match:
                                    f_raw, d_raw, m_str = match.groups()
                                    monto = float(m_str.replace('-', '').replace(',', ''))
                                    if monto == 0: continue
                                    tipo, cat, desc = aplicar_reglas(d_raw.strip(), monto, "Gasto" if m_str.endswith('-') else "Ingreso")
                                    dia, mes = f_raw.split('-')
                                    movs_extraidos.append({"fecha": f"2026-{mes}-{dia}", "tipo": tipo, "categoria": cat, "descripcion": desc, "monto": monto, "origen": archivo.name})

# ==========================================
# INTERFAZ CON BLOQUEO ANTI-ERRORES
# ==========================================
if movs_extraidos:
    df_st = pd.DataFrame(movs_extraidos).sort_values(by="fecha", ascending=False)
    st.session_state['staging_data'] = df_st
    st.success(f"✅ {len(movs_extraidos)} movimientos procesados.")

if 'staging_data' in st.session_state and not st.session_state['staging_data'].empty:
    st.markdown("### ✍️ Vista Previa y Edición")
    
    # 🌟 TRUCO: Creamos un contenedor vacío que agrupará la tabla y los botones
    zona_edicion = st.empty()
    
    # Metemos todo dentro del contenedor
    with zona_edicion.container():
        df_editado = st.data_editor(
            st.session_state['staging_data'], 
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "tipo": st.column_config.SelectboxColumn("Tipo", options=["Gasto", "Ingreso", "Ahorro"], required=True),
                "categoria": st.column_config.SelectboxColumn("Categoría", options=CATEGORIAS_GASTOS + CATEGORIAS_INGRESOS_BASE + CATEGORIAS_AHORRO, required=True),
                "monto": st.column_config.NumberColumn("Monto", format="S/ %.2f", min_value=0.0),
                "origen": st.column_config.TextColumn("Archivo Origen", disabled=True) # <-- ESTA LÍNEA
            }
        )
        
        c_bot1, c_bot2 = st.columns([1, 4])
        btn_guardar = c_bot1.button("💾 Guardar Todo en Neon", type="primary")
        btn_cancelar = c_bot2.button("❌ Cancelar Carga")

    # Si alguien cancela, limpiamos los datos y recargamos
    if btn_cancelar:
        st.session_state['staging_data'] = pd.DataFrame()
        st.rerun()

    # Si alguien presiona Guardar...
    if btn_guardar:
        # 1. ¡DESAPARECEMOS LA TABLA Y BOTONES AL INSTANTE PARA BLOQUEAR LA PANTALLA!
        zona_edicion.empty() 
        
        # 2. Mostramos el proceso de guardado sin que nada más estorbe
        with st.spinner("Conectando a la base de datos en la nube..."):
            conn = conectar_bd()
            cur = conn.cursor()
            
        total_filas = len(df_editado)
        barra_progreso = st.progress(0)
        texto_progreso = st.empty() 
        
        for i, (_, row_fin) in enumerate(df_editado.iterrows()):
            texto_progreso.text(f"⏳ Guardando movimiento {i + 1} de {total_filas}...")
            barra_progreso.progress(int(((i + 1) / total_filas) * 100))
            
            p_calc = obtener_periodo(str(row_fin['fecha'])[:10])
            cur.execute("INSERT INTO movimientos (tipo, categoria, monto, fecha, periodo, descripcion, origen) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (row_fin['tipo'], row_fin['categoria'], row_fin['monto'], str(row_fin['fecha'])[:10], p_calc, row_fin['descripcion'], row_fin.get('origen', 'Manual')))
        
        conn.commit()
        cur.close()
        conn.close()
        
        texto_progreso.empty()
        barra_progreso.empty()
        st.session_state['staging_data'] = pd.DataFrame() 
        st.success(f"¡{total_filas} movimientos cargados a tu base de datos!")
        
        time.sleep(1.5) 
        st.rerun()