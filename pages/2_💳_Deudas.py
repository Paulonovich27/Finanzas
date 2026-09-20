# pages/2_💳_Deudas.py
import streamlit as st
import pandas as pd
from database import conectar_bd
from config import DEUDAS_CATEGORIAS

st.set_page_config(page_title="Control de Deudas", page_icon="💳", layout="wide")

if 'deuda_a_editar' not in st.session_state: st.session_state.deuda_a_editar = None
if 'deuda_a_borrar' not in st.session_state: st.session_state.deuda_a_borrar = None

st.subheader("💳 Control de Deudas")

conn = conectar_bd()
cur = conn.cursor()
cur.execute("SELECT * FROM deudas")
columnas = [desc[0] for desc in cur.description]
datos = cur.fetchall()
df_deudas = pd.DataFrame(datos, columns=columnas)
cur.close()
conn.close()

st.markdown("""
    <div style="background-color: #1e1e1e; padding: 10px; border-radius: 5px; color: white; display: flex; text-align: center; font-weight: bold;">
        <div style="flex: 2;">Categoría</div>
        <div style="flex: 1.5;">Tipo</div>
        <div style="flex: 1.5;">Pendiente</div>
        <div style="flex: 1.5;">Cuotas</div>
        <div style="flex: 1.5;">Mensual</div>
        <div style="flex: 1.5;">Acciones</div>
    </div>
""", unsafe_allow_html=True)
st.write("")

if not df_deudas.empty:
    for _, row in df_deudas.iterrows():
        c1, c2, c3, c4, c5, c6 = st.columns([2, 1.5, 1.5, 1.5, 1.5, 1.5])
        c1.markdown(f"<div style='text-align: center; margin-top: 10px;'><b>{row['categoria']}</b></div>", unsafe_allow_html=True)
        c2.markdown(f"<div style='text-align: center; margin-top: 10px;'>{row['tipo_deuda']}</div>", unsafe_allow_html=True)
        c3.markdown(f"<div style='text-align: center; margin-top: 10px;'>S/ {row['capital_pendiente']:.2f}</div>", unsafe_allow_html=True)
        c4.markdown(f"<div style='text-align: center; margin-top: 10px;'>{row['cuota_actual']} / {row['cuota_total']}</div>", unsafe_allow_html=True)
        c5.markdown(f"<div style='text-align: center; margin-top: 10px;'>S/ {row['pago_mensual']:.2f}</div>", unsafe_allow_html=True)
        
        with c6:
            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.button("✏️", key=f"edit_d_{row['categoria']}"):
                st.session_state.deuda_a_editar, st.session_state.deuda_a_borrar = row['categoria'], None
            if col_btn2.button("🗑️", key=f"del_d_{row['categoria']}"):
                st.session_state.deuda_a_borrar, st.session_state.deuda_a_editar = row['categoria'], None
        st.markdown("<hr style='margin: 5px 0px; opacity: 0.2;'>", unsafe_allow_html=True)
else:
    st.info("No tienes deudas registradas.")

st.divider()

if st.session_state.deuda_a_borrar:
    st.error(f"⚠️ **¿Eliminar permanentemente la deuda '{st.session_state.deuda_a_borrar}'?**")
    c_conf1, c_conf2 = st.columns([1, 4])
    if c_conf1.button("✔️ Sí, eliminar"):
        conn = conectar_bd()
        cur = conn.cursor()
        cur.execute("DELETE FROM deudas WHERE categoria = %s", (st.session_state.deuda_a_borrar,))
        conn.commit()
        cur.close()
        conn.close()
        st.session_state.deuda_a_borrar = None
        st.success("Deuda eliminada.")
        st.rerun()
    if c_conf2.button("❌ Cancelar"):
        st.session_state.deuda_a_borrar = None
        st.rerun()

elif st.session_state.deuda_a_editar:
    st.markdown(f"### ✏️ Editando: {st.session_state.deuda_a_editar}")
    row_edit = df_deudas[df_deudas['categoria'] == st.session_state.deuda_a_editar].iloc[0]
    
    with st.form("form_edit_deuda_inferior"):
        e_tipo = st.selectbox("Tipo de Deuda", ["Flexible", "Bancaria / Cuotas"], index=0 if row_edit['tipo_deuda']=="Flexible" else 1)
        
        col_f1, col_f2 = st.columns(2)
        e_orig = col_f1.number_input("Monto Original (S/)", value=float(row_edit['monto_original']), format="%.2f")
        e_pend = col_f2.number_input("Capital Pendiente (S/)", value=float(row_edit['capital_pendiente']), format="%.2f")
        
        col_f3, col_f4, col_f5 = st.columns(3)
        val_ctot = int(row_edit['cuota_total']) if row_edit['cuota_total'] and row_edit['cuota_total'] > 0 else 1
        val_cact = int(row_edit['cuota_actual']) if row_edit['cuota_actual'] and row_edit['cuota_actual'] >= 0 else 0
        
        e_ctot = col_f3.number_input("Cuotas Totales", value=val_ctot, min_value=1)
        e_cact = col_f4.number_input("Cuota Actual", value=val_cact, min_value=0)
        e_pago = col_f5.number_input("Pago Mensual (S/)", value=float(row_edit['pago_mensual']), format="%.2f")
        
        if st.form_submit_button("💾 Guardar", type="primary"):
            conn = conectar_bd()
            cur = conn.cursor()
            cur.execute("UPDATE deudas SET tipo_deuda=%s, monto_original=%s, capital_pendiente=%s, cuota_total=%s, cuota_actual=%s, pago_mensual=%s WHERE categoria=%s",
                        (e_tipo, e_orig, e_pend, e_ctot, e_cact, e_pago, st.session_state.deuda_a_editar))
            conn.commit()
            cur.close()
            conn.close()
            st.session_state.deuda_a_editar = None
            st.success("¡Deuda actualizada!")
            st.rerun()
    if st.button("❌ Cerrar Edición"): # BOTÓN CORREGIDO FUERA DEL FORM
        st.session_state.deuda_a_editar = None
        st.rerun()

else:
    with st.expander("📝 Formulario de Nueva Deuda"):
        with st.form("form_crear_deuda_nueva"):
            d_cat = st.selectbox("Categoría de Deuda", DEUDAS_CATEGORIAS)
            d_tipo = st.selectbox("Tipo", ["Flexible", "Bancaria / Cuotas"])
            d_orig = st.number_input("Monto Original (S/)", min_value=0.0, format="%.2f")
            d_pend = st.number_input("Pendiente (S/)", min_value=0.0, format="%.2f")
            d_ctot = st.number_input("Cuotas Tot", min_value=1, value=12)
            d_cact = st.number_input("Cuota Actual", min_value=0, value=1)
            d_pago = st.number_input("Pago Mensual (S/)", min_value=0.0, format="%.2f")
            
            if st.form_submit_button("Guardar"):
                conn = conectar_bd()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO deudas (categoria, tipo_deuda, monto_original, capital_pendiente, cuota_total, cuota_actual, pago_mensual)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (categoria) DO NOTHING
                """, (d_cat, d_tipo, d_orig, d_pend, d_ctot, d_cact, d_pago))
                conn.commit()
                cur.close()
                conn.close()
                st.success("¡Registrada!")
                st.rerun()