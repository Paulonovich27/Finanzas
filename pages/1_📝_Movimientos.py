# pages/1_📝_Movimientos.py
import streamlit as st
import pandas as pd
import math
from datetime import datetime
from config import CATEGORIAS_GASTOS, CATEGORIAS_INGRESOS_BASE, CATEGORIAS_AHORRO, obtener_periodo
from database import conectar_bd, cargar_movimientos

st.set_page_config(page_title="Movimientos", page_icon="📝", layout="wide")

# Inicializar estados
if 'pagina_movs' not in st.session_state: st.session_state.pagina_movs = 1
if 'mov_a_editar' not in st.session_state: st.session_state.mov_a_editar = None
if 'mov_a_borrar' not in st.session_state: st.session_state.mov_a_borrar = None
if 'mov_agregar' not in st.session_state: st.session_state.mov_agregar = False

st.subheader("📝 Gestión de Movimientos")

df_movs = cargar_movimientos()

if not df_movs.empty:
    col_filtro1, col_filtro2 = st.columns([1, 2])
    
    periodos_disp = ["Todos los meses"] + sorted(df_movs['periodo'].dropna().unique().tolist(), reverse=True)
    mes_filtro = col_filtro1.selectbox("📅 Filtrar por periodo:", periodos_disp)
    
    with col_filtro2.form("form_busqueda"):
        c_busq, c_btn = st.columns([4, 1])
        texto_busqueda = c_busq.text_input("🔍 Buscar por descripción o categoría:")
        submit_buscar = c_btn.form_submit_button("Buscar")
    
    df_gest = df_movs[df_movs['periodo'] == mes_filtro] if mes_filtro != "Todos los meses" else df_movs
    
    if texto_busqueda:
        df_gest = df_gest[
            df_gest['descripcion'].str.contains(texto_busqueda, case=False, na=False) |
            df_gest['categoria'].str.contains(texto_busqueda, case=False, na=False)
        ]
        if submit_buscar: st.session_state.pagina_movs = 1
else:
    df_gest = pd.DataFrame()
    
ITEMS_POR_PAGINA = 10
total_items = len(df_gest)
total_paginas = max(1, math.ceil(total_items / ITEMS_POR_PAGINA))

if st.session_state.pagina_movs > total_paginas: st.session_state.pagina_movs = 1

if total_items > 0:
    c_pag1, c_pag2, c_pag3 = st.columns([1, 2, 1])
    if c_pag1.button("⬅️ Anterior") and st.session_state.pagina_movs > 1:
        st.session_state.pagina_movs -= 1
        st.rerun()
    c_pag2.markdown(f"<div style='text-align: center; margin-top: 5px; color: #aaa;'>Página <b>{st.session_state.pagina_movs}</b> de <b>{total_paginas}</b> ({total_items} registros encontrados)</div>", unsafe_allow_html=True)
    if c_pag3.button("Siguiente ➡️") and st.session_state.pagina_movs < total_paginas:
        st.session_state.pagina_movs += 1
        st.rerun()

inicio_idx = (st.session_state.pagina_movs - 1) * ITEMS_POR_PAGINA
df_pagina = df_gest.iloc[inicio_idx : inicio_idx + ITEMS_POR_PAGINA]

st.markdown("""
    <div style="background-color: #1e1e1e; padding: 10px; border-radius: 5px; color: white; display: flex; text-align: center; font-weight: bold;">
        <div style="flex: 1.5;">Fecha</div>
        <div style="flex: 1.5;">Tipo</div>
        <div style="flex: 2;">Categoría</div>
        <div style="flex: 3;">Descripción</div>
        <div style="flex: 1.5;">Monto</div>
        <div style="flex: 1.5;">Acciones</div>
    </div>
""", unsafe_allow_html=True)
st.write("")

if not df_pagina.empty:
    for _, row in df_pagina.iterrows():
        c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1.5, 2, 3, 1.5, 1.5])
        c1.markdown(f"<div style='text-align: center; margin-top: 10px;'>{str(row['fecha'])[:10]}</div>", unsafe_allow_html=True)
        c2.markdown(f"<div style='text-align: center; margin-top: 10px;'>{row['tipo']}</div>", unsafe_allow_html=True)
        c3.markdown(f"<div style='text-align: center; margin-top: 10px;'>{row['categoria']}</div>", unsafe_allow_html=True)
        c4.markdown(f"<div style='text-align: center; margin-top: 10px;'>{row['descripcion']}</div>", unsafe_allow_html=True)
        c5.markdown(f"<div style='text-align: center; margin-top: 10px;'>S/ {row['monto']:.2f}</div>", unsafe_allow_html=True)
        
        with c6:
            col_b1, col_b2 = st.columns(2)
            if col_b1.button("✏️", key=f"edit_m_{row['id']}"):
                st.session_state.mov_a_editar, st.session_state.mov_a_borrar, st.session_state.mov_agregar = row['id'], None, False
            if col_b2.button("🗑️", key=f"del_m_{row['id']}"):
                st.session_state.mov_a_borrar, st.session_state.mov_a_editar, st.session_state.mov_agregar = row['id'], None, False
        st.markdown("<hr style='margin: 5px 0px; opacity: 0.2;'>", unsafe_allow_html=True)
else:
    st.info("No hay registros en esta vista.")

st.divider()

c_btn_agg, _ = st.columns([1, 4])
if c_btn_agg.button("➕ Agregar Nuevo Movimiento", type="primary"):
    st.session_state.mov_agregar, st.session_state.mov_a_editar, st.session_state.mov_a_borrar = True, None, None

if st.session_state.mov_a_borrar:
    row_del = df_gest[df_gest['id'] == st.session_state.mov_a_borrar].iloc[0]
    st.error(f"⚠️ **¿Eliminar permanentemente el movimiento de S/ {row_del['monto']:.2f} ({row_del['categoria']})?**")
    c_conf1, c_conf2 = st.columns([1, 4])
    if c_conf1.button("✔️ Sí, eliminar"):
        conn = conectar_bd()
        cur = conn.cursor()
        cur.execute("DELETE FROM movimientos WHERE id = %s", (int(st.session_state.mov_a_borrar),))
        conn.commit()
        cur.close()
        conn.close()
        st.session_state.mov_a_borrar = None
        st.success("Movimiento eliminado.")
        st.rerun()
    if c_conf2.button("❌ Cancelar"):
        st.session_state.mov_a_borrar = None
        st.rerun()

elif st.session_state.mov_a_editar:
    st.markdown(f"### ✏️ Editando Movimiento (ID: {st.session_state.mov_a_editar})")
    row_edit = df_gest[df_gest['id'] == st.session_state.mov_a_editar].iloc[0]
    
    with st.form("form_edit_mov"):
        n_tipo = st.selectbox("Tipo", ["Gasto", "Ingreso", "Ahorro"], index=["Gasto", "Ingreso", "Ahorro"].index(row_edit['tipo']))
        lista_g = CATEGORIAS_INGRESOS_BASE if n_tipo == "Ingreso" else (CATEGORIAS_AHORRO if n_tipo == "Ahorro" else CATEGORIAS_GASTOS)
        cat_idx = lista_g.index(row_edit['categoria']) if row_edit['categoria'] in lista_g else 0
        n_cat = st.selectbox("Categoría", lista_g, index=cat_idx)
        
        col_f1, col_f2 = st.columns(2)
        n_mon = col_f1.number_input("Monto (S/)", value=float(row_edit['monto']), format="%.2f")
        f_val = datetime.strptime(str(row_edit['fecha'])[:10], "%Y-%m-%d").date()
        n_fec = col_f2.date_input("Fecha", value=f_val)
        n_desc = st.text_input("Descripción", value=str(row_edit['descripcion']))
        
        c_bot1, c_bot2 = st.columns([1, 4])
        if c_bot1.form_submit_button("💾 Guardar Cambios", type="primary"):
            f_str = n_fec.strftime("%Y-%m-%d")
            conn = conectar_bd()
            cur = conn.cursor()
            cur.execute("UPDATE movimientos SET tipo=%s, categoria=%s, monto=%s, fecha=%s, periodo=%s, descripcion=%s WHERE id=%s", 
                        (n_tipo, n_cat, n_mon, f_str, obtener_periodo(f_str), n_desc, int(st.session_state.mov_a_editar)))
            conn.commit()
            cur.close()
            conn.close()
            st.session_state.mov_a_editar = None
            st.success("¡Movimiento actualizado!")
            st.rerun()
    if st.button("❌ Cancelar Edición"): # BOTÓN CORREGIDO FUERA DEL FORM
        st.session_state.mov_a_editar = None
        st.rerun()

elif st.session_state.mov_agregar:
    st.markdown("### 📝 Registrar Nuevo Movimiento")
    with st.form("form_agg_mov"):
        tipo = st.selectbox("Tipo de Movimiento", ["Gasto", "Ingreso", "Ahorro"])
        categoria = st.selectbox("Categoría", CATEGORIAS_INGRESOS_BASE if tipo == "Ingreso" else (CATEGORIAS_AHORRO if tipo == "Ahorro" else CATEGORIAS_GASTOS))
        
        col_f1, col_f2 = st.columns(2)
        monto = col_f1.number_input("Monto (S/)", min_value=0.0, format="%.2f")
        fecha = col_f2.date_input("Fecha de Operación", value=datetime.now())
        descripcion = st.text_input("Descripción")
        
        if st.form_submit_button("💾 Guardar", type="primary"):
            f_str = fecha.strftime("%Y-%m-%d")
            conn = conectar_bd()
            cur = conn.cursor()
            cur.execute("INSERT INTO movimientos (tipo, categoria, monto, fecha, periodo, descripcion) VALUES (%s, %s, %s, %s, %s, %s)",
                        (tipo, categoria, monto, f_str, obtener_periodo(f_str), descripcion))
            conn.commit()
            cur.close()
            conn.close()
            st.session_state.mov_agregar = False
            st.success("¡Movimiento guardado!")
            st.rerun()
    if st.button("❌ Cerrar Panel"): # BOTÓN CORREGIDO FUERA DEL FORM
        st.session_state.mov_agregar = False
        st.rerun()