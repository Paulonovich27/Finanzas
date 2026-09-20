# pages/1_📝_Movimientos.py
import streamlit as st
import pandas as pd
import math
import time
from database import cargar_movimientos, conectar_bd
from config import CATEGORIAS_GASTOS, CATEGORIAS_INGRESOS_BASE, CATEGORIAS_AHORRO

st.set_page_config(page_title="Movimientos", page_icon="📝", layout="wide")

# --- ESTADOS DE SESIÓN ---
if 'mov_a_editar' not in st.session_state: st.session_state.mov_a_editar = None
if 'mov_a_borrar' not in st.session_state: st.session_state.mov_a_borrar = None

# --- CARGAR DATOS ---
df = cargar_movimientos()

st.title("📝 Gestión de Movimientos")

if df.empty:
    st.info("Aún no tienes movimientos registrados. Ve a 'Carga Masiva' para empezar.")
else:
    # ==========================================
    # 1. BARRA DE FILTROS (DISEÑO MEJORADO)
    # ==========================================
    st.markdown("### 🔍 Filtros de Búsqueda")
    col_f1, col_f2, col_f3 = st.columns([1.5, 2, 1.5])
    
    with col_f1:
        periodos = ["Todos"] + sorted(df['periodo'].dropna().unique().tolist(), reverse=True)
        filtro_periodo = st.selectbox("📅 Periodo:", periodos)
        
    with col_f2:
        filtro_texto = st.text_input("🔎 Buscar descripción o categoría:")
        
    with col_f3:
        # Si la columna origen no existe por alguna razón, evitamos error
        origenes = ["Todos"] + sorted(df['origen'].dropna().unique().tolist()) if 'origen' in df.columns else ["Todos"]
        filtro_origen = st.selectbox("📂 Archivo de Origen:", origenes)

    # Aplicar filtros
    df_filtrado = df.copy()
    if filtro_periodo != "Todos":
        df_filtrado = df_filtrado[df_filtrado['periodo'] == filtro_periodo]
    if filtro_origen != "Todos":
        df_filtrado = df_filtrado[df_filtrado['origen'] == filtro_origen] if 'origen' in df_filtrado.columns else df_filtrado
    if filtro_texto:
        df_filtrado = df_filtrado[df_filtrado.apply(lambda row: filtro_texto.lower() in str(row['descripcion']).lower() or filtro_texto.lower() in str(row['categoria']).lower(), axis=1)]

    # ==========================================
    # 2. PAGINACIÓN
    # ==========================================
    filas_por_pagina = 15
    total_paginas = math.ceil(len(df_filtrado) / filas_por_pagina) if len(df_filtrado) > 0 else 1
    
    if 'pagina_actual' not in st.session_state: st.session_state.pagina_actual = 1
    # Asegurar que la página actual no se salga del rango tras filtrar
    if st.session_state.pagina_actual > total_paginas: st.session_state.pagina_actual = 1

    st.markdown("<br>", unsafe_allow_html=True)
    c_pag1, c_pag2, c_pag3 = st.columns([1, 2, 1])
    with c_pag1:
        if st.button("⬅️ Anterior", disabled=(st.session_state.pagina_actual == 1), use_container_width=True):
            st.session_state.pagina_actual -= 1
            st.rerun()
    with c_pag2:
        st.markdown(f"<div style='text-align: center; padding-top: 5px;'>Página <b>{st.session_state.pagina_actual}</b> de {total_paginas} <span style='color:gray;'>({len(df_filtrado)} registros)</span></div>", unsafe_allow_html=True)
    with c_pag3:
        if st.button("Siguiente ➡️", disabled=(st.session_state.pagina_actual == total_paginas), use_container_width=True):
            st.session_state.pagina_actual += 1
            st.rerun()

    inicio_idx = (st.session_state.pagina_actual - 1) * filas_por_pagina
    df_pagina = df_filtrado.iloc[inicio_idx:inicio_idx + filas_por_pagina]

    # ==========================================
    # 3. TABLA DE DATOS
    # ==========================================
    st.markdown("""
        <div style="background-color: #1e1e1e; padding: 10px; border-radius: 5px; color: white; display: flex; text-align: center; font-weight: bold; margin-bottom: 10px;">
            <div style="flex: 1.5;">Fecha</div>
            <div style="flex: 1.5;">Tipo</div>
            <div style="flex: 2;">Categoría</div>
            <div style="flex: 3;">Descripción</div>
            <div style="flex: 1.5;">Origen</div>
            <div style="flex: 1.5;">Monto</div>
            <div style="flex: 1.5;">Acciones</div>
        </div>
    """, unsafe_allow_html=True)

    if not df_pagina.empty:
        for _, row in df_pagina.iterrows():
            c1, c2, c3, c4, c5, c6, c7 = st.columns([1.5, 1.5, 2, 3, 1.5, 1.5, 1.5])
            c1.markdown(f"<div style='text-align: center; margin-top: 10px;'>{str(row['fecha'])[:10]}</div>", unsafe_allow_html=True)
            
            # Colores para Tipo
            color_tipo = "#4CAF50" if row['tipo'] == "Ingreso" else "#F44336" if row['tipo'] == "Gasto" else "#2196F3"
            c2.markdown(f"<div style='text-align: center; margin-top: 10px; color: {color_tipo};'>{row['tipo']}</div>", unsafe_allow_html=True)
            
            c3.markdown(f"<div style='text-align: center; margin-top: 10px;'>{row['categoria']}</div>", unsafe_allow_html=True)
            c4.markdown(f"<div style='text-align: center; margin-top: 10px;'>{row['descripcion']}</div>", unsafe_allow_html=True)
            
            origen_txt = row['origen'] if 'origen' in row and pd.notna(row['origen']) else 'Manual'
            c5.markdown(f"<div style='text-align: center; margin-top: 10px; font-size: 0.85em; color: #888;'>{origen_txt}</div>", unsafe_allow_html=True)
            c6.markdown(f"<div style='text-align: center; margin-top: 10px; font-weight: bold;'>S/ {row['monto']:.2f}</div>", unsafe_allow_html=True)
            
            with c7:
                col_b1, col_b2 = st.columns(2)
                if col_b1.button("✏️", key=f"edit_m_{row['id']}", help="Editar registro"):
                    st.session_state.mov_a_editar, st.session_state.mov_a_borrar = row['id'], None
                if col_b2.button("🗑️", key=f"del_m_{row['id']}", help="Borrar registro"):
                    st.session_state.mov_a_borrar, st.session_state.mov_a_editar = row['id'], None
            st.markdown("<hr style='margin: 5px 0px; opacity: 0.2;'>", unsafe_allow_html=True)
    else:
        st.warning("No se encontraron registros con esos filtros.")

    # ==========================================
    # 4. ACTUALIZACIÓN MASIVA INTELIGENTE (TABLA AGRUPADA)
    # ==========================================
    st.divider()
    st.markdown("### 🛠️ Actualización Masiva de Reglas")
    st.info("Selecciona un grupo de gastos en la tabla marcando la casilla izquierda para actualizar todos sus registros a la vez.")
    
    # Agrupar los datos por Tipo, Categoría y Descripción
    df_grouped = df.groupby(['tipo', 'categoria', 'descripcion']).size().reset_index(name='cantidad_registros')
    # Ordenar por los más repetidos primero
    df_grouped = df_grouped.sort_values(by='cantidad_registros', ascending=False).reset_index(drop=True)
    
    # Insertar columna de check
    df_grouped.insert(0, "Seleccionar", False)
    
    df_seleccion = st.data_editor(
        df_grouped,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Seleccionar": st.column_config.CheckboxColumn("Seleccionar", default=False),
            "tipo": st.column_config.TextColumn("Tipo Actual", disabled=True),
            "categoria": st.column_config.TextColumn("Categoría Actual", disabled=True),
            "descripcion": st.column_config.TextColumn("Descripción Actual", disabled=True),
            "cantidad_registros": st.column_config.NumberColumn("Cantidad de Datos", disabled=True)
        }
    )
    
    seleccionados = df_seleccion[df_seleccion["Seleccionar"]]
    
    if len(seleccionados) == 1:
        row_sel = seleccionados.iloc[0]
        old_tipo, old_cat, old_desc = row_sel['tipo'], row_sel['categoria'], row_sel['descripcion']
        
        st.markdown(f"**Modificando {row_sel['cantidad_registros']} registros de:** `{old_desc}`")
        
        c_m1, c_m2, c_m3 = st.columns([1.5, 2, 2.5])
        with c_m1:
            nuevo_tipo = st.selectbox("Nuevo Tipo:", ["Gasto", "Ingreso", "Ahorro"], index=["Gasto", "Ingreso", "Ahorro"].index(old_tipo) if old_tipo in ["Gasto", "Ingreso", "Ahorro"] else 0)
        with c_m2:
            todas_cats = CATEGORIAS_GASTOS + CATEGORIAS_INGRESOS_BASE + CATEGORIAS_AHORRO
            idx_cat = todas_cats.index(old_cat) if old_cat in todas_cats else 0
            nueva_cat = st.selectbox("Nueva Categoría:", todas_cats, index=idx_cat)
        with c_m3:
            nueva_desc = st.text_input("Nueva Descripción:", value=old_desc)
            
        if st.button("🚀 Confirmar Cambios", type="primary"):
            with st.spinner("Actualizando registros en la base de datos..."):
                conn = conectar_bd()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE movimientos SET tipo = %s, categoria = %s, descripcion = %s WHERE tipo = %s AND categoria = %s AND descripcion = %s", 
                    (nuevo_tipo, nueva_cat, nueva_desc, old_tipo, old_cat, old_desc)
                )
                filas_afectadas = cur.rowcount
                conn.commit()
                cur.close()
                conn.close()
                
            st.success(f"¡Se actualizaron {filas_afectadas} registros exitosamente!")
            time.sleep(1.5)
            st.rerun()
            
    elif len(seleccionados) > 1:
        st.warning("⚠️ Por favor, selecciona solo un grupo a la vez marcando una sola casilla.")

# ==========================================
# 5. ZONA DE PELIGRO
# ==========================================
st.divider()
with st.expander("⚠️ ZONA DE PELIGRO: Borrar Base de Datos"):
    st.error("Al presionar este botón, se eliminarán TODOS los movimientos de la base de datos de Neon de forma permanente.")
    c_borrar1, c_borrar2 = st.columns([1, 4])
    if c_borrar1.button("🗑️ Borrar TODOS los datos", type="primary"):
        conn = conectar_bd()
        cur = conn.cursor()
        cur.execute("DELETE FROM movimientos")
        conn.commit()
        cur.close()
        conn.close()
        st.success("¡Base de datos reseteada con éxito!")
        time.sleep(1)
        st.rerun()