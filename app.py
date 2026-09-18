import streamlit as st
import pandas as pd
from datetime import datetime
import psycopg2

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Mi Gestor Financiero", page_icon="💰", layout="wide")

# --- REGLA DE NEGOCIO: DÍA DE CORTE ---
DIA_CORTE = 25

CATEGORIAS_INGRESOS_BASE = ["Sueldo", "Sueldo Esposa", "Ayuda Papá (Colegio)", "Otros Ingresos"]
CATEGORIAS_GASTOS = [
    "Hipoteca", "Mantenimiento + agua", "Luz", "Gas Pa", "Gas Paul",
    "Internet", "Celular Paul", "Celular Fiorella", "Colegio Joanne", "Colegio Joaquin",
    "Comida", "Supermercado", "Mercado", "Pasajes Paul", "Pasajes Fiorella",
    "Mapfre", "Prestamo personal (banco)", "Prestamo Yape", "Mapfre deuda",
    "Prestamo Makoto", "Prestamo Mamá", "Prestamo Hijos"
]
CATEGORIAS_AHORRO = ["Fondo de Emergencia", "Plazo Fijo", "Caja de Ahorros", "Inversiones"]
DEUDAS_CATEGORIAS = ["Hipoteca", "Prestamo personal (banco)", "Prestamo Yape", "Mapfre deuda", "Prestamo Makoto", "Prestamo Mamá", "Prestamo Hijos"]

def obtener_periodo(fecha_texto):
    try:
        dt = datetime.strptime(str(fecha_texto)[:10], "%Y-%m-%d")
        if dt.day >= DIA_CORTE:
            if dt.month == 12:
                return f"{dt.year + 1}-01"
            else:
                return f"{dt.year}-{dt.month + 1:02d}"
        else:
            return f"{dt.year}-{dt.month:02d}"
    except:
        return str(fecha_texto)[:7]

# --- CONEXIÓN A NEON (POSTGRESQL) ---
def conectar_bd():
    try:
        conexion = psycopg2.connect(st.secrets["NEON_URL"])
        return conexion
    except Exception as e:
        st.error(f"Error al conectar con la base de datos en Neon: {e}")
        st.stop()

def inicializar_tablas():
    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS movimientos (
            id SERIAL PRIMARY KEY,
            tipo TEXT, categoria TEXT, monto REAL, fecha TEXT, periodo TEXT, descripcion TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS deudas (
            categoria TEXT PRIMARY KEY,
            tipo_deuda TEXT,
            monto_original REAL,
            capital_pendiente REAL,
            cuota_total INTEGER,
            cuota_actual INTEGER,
            pago_mensual REAL
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

inicializar_tablas()

def cargar_movimientos():
    conn = conectar_bd()
    df = pd.read_sql("SELECT id, tipo, categoria, monto, fecha, periodo, descripcion FROM movimientos ORDER BY fecha DESC", conn)
    conn.close()
    return df

# --- INTERFAZ PRINCIPAL (STREAMLIT) ---
st.title("📊 Mi Gestor Financiero Familiar")

df_movs = cargar_movimientos()

# Menú lateral ampliado con el Predictor
st.sidebar.header("Control Panel")
accion = st.sidebar.selectbox("¿Qué deseas hacer?", ["Resumen y Smart Insights", "💡 Predictor de Excedentes", "Registrar Movimiento", "Estado de Deudas"])

if not df_movs.empty:
    periodos_disponibles = ["Todos los meses"] + sorted(df_movs['periodo'].dropna().unique().tolist(), reverse=True)
    mes_seleccionado = st.sidebar.selectbox("Filtrar por Flujo Mensual", periodos_disponibles)
    
    if mes_seleccionado != "Todos los meses":
        df_filtrado = df_movs[df_movs['periodo'] == mes_seleccionado]
    else:
        df_filtrado = df_movs
else:
    mes_seleccionado = "Todos los meses"
    df_filtrado = pd.DataFrame()

# --- 1. RESUMEN Y SMART INSIGHTS ---
if accion == "Resumen y Smart Insights":
    st.subheader(f"Resumen Financiero: {mes_seleccionado}")
    
    if not df_filtrado.empty:
        ingresos = df_filtrado[df_filtrado['tipo'] == 'Ingreso']['monto'].sum()
        gastos = df_filtrado[df_filtrado['tipo'] == 'Gasto']['monto'].sum()
        ahorros = df_filtrado[df_filtrado['tipo'] == 'Ahorro']['monto'].sum()
        saldo = ingresos - gastos - ahorros
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Ingresos", f"S/ {ingresos:.2f}")
        col2.metric("Gastos", f"S/ {gastos:.2f}")
        col3.metric("Ahorros", f"S/ {ahorros:.2f}")
        col4.metric("Saldo Libre", f"S/ {saldo:.2f}", delta=f"S/ {saldo:.2f}")
        
        st.divider()
        st.subheader("💡 Diagnóstico Inteligente (Smart Insights)")
        
        gasto_comida = df_filtrado[(df_filtrado['tipo'] == 'Gasto') & (df_filtrado['categoria'].isin(['Comida', 'Supermercado', 'Mercado']))]['monto'].sum()
        if gasto_comida == 0 and not df_filtrado.empty:
            st.warning("⚠️ **Alerta de Falsa Liquidez:** No registras gastos en alimentación (Mercado/Supermercado) para este periodo.")
        
        yapes_pequeños = df_filtrado[(df_filtrado['categoria'] == 'Prestamo Yape') | ((df_filtrado['tipo'] == 'Gasto') & (df_filtrado['monto'] < 30))]
        total_hormiga = yapes_pequeños['monto'].sum()
        if total_hormiga > 300:
            st.info(f"🐜 **Gastos Hormiga Detectados:** Tienes acumulados S/ {total_hormiga:.2f} en microtransacciones este mes.")
            
        if saldo > 1000:
            st.success(f"✅ **Buen Flujo de Caja:** Cuentas con un excedente saludable de S/ {saldo:.2f}. Revisa el Predictor en el menú.")
        elif saldo < 0:
            st.error(f"🚨 **Déficit Financiero:** Estás gastando más de lo que ingresas por S/ {abs(saldo):.2f}.")
            
        st.divider()
        st.markdown("### 📋 Detalle de Movimientos")
        st.dataframe(df_filtrado[['fecha', 'periodo', 'tipo', 'categoria', 'descripcion', 'monto']], use_container_width=True)
    else:
        st.info("No hay movimientos registrados todavía.")

# --- 2. PREDICTOR DE EXCEDENTES ---
elif accion == "💡 Predictor de Excedentes":
    st.subheader("💡 Asistente Predictivo de Excedentes")
    
    if mes_seleccionado == "Todos los meses":
        st.warning("⚠️ Por favor selecciona un **mes específico** en el menú lateral para evaluar el predictor de flujo real.")
    else:
        ingresos = df_filtrado[df_filtrado['tipo'] == 'Ingreso']['monto'].sum()
        gastos = df_filtrado[df_filtrado['tipo'] == 'Gasto']['monto'].sum()
        ahorros = df_filtrado[df_filtrado['tipo'] == 'Ahorro']['monto'].sum()
        saldo_disponible = ingresos - gastos - ahorros
        
        st.metric(f"Excedente proyectado para {mes_seleccionado}", f"S/ {saldo_disponible:.2f}")
        
        if saldo_disponible <= 0:
            st.info("No cuentas con liquidez excedente en este periodo para destinar a deudas extra o inversiones.")
        else:
            UMBRAL_MINIMO = 800.0
            
            if saldo_disponible < UMBRAL_MINIMO:
                st.warning(f"⚠️ **Prioriza tu Liquidez:** Tienes S/ {saldo_disponible:.2f}, pero al estar por debajo del umbral seguro de S/ {UMBRAL_MINIMO:.0f}, la mejor opción es guardarlo como fondo de emergencia ante imprevistos.")
                if st.button("Guardar como Fondo de Emergencia"):
                    conn = conectar_bd()
                    cur = conn.cursor()
                    cur.execute("INSERT INTO movimientos (tipo, categoria, monto, fecha, periodico, descripcion) VALUES (%s, %s, %s, %s, %s, %s)",
                                ("Ahorro", "Fondo de Emergencia", saldo_disponible, f"{mes_seleccionado}-01", mes_seleccionado, "Ahorro por seguridad (Predictor)"))
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success("¡Guardado exitosamente!")
                    st.rerun()
            else:
                st.info("✅ Tienes un excedente saludable superior a S/ 800. Elige tu estrategia:")
                
                # Cargar deudas de la BD
                conn = conectar_bd()
                df_deudas = pd.read_sql("SELECT categoria, tipo_deuda, monto_original, capital_pendiente, pago_mensual FROM deudas", conn)
                conn.close()
                
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    st.markdown("### 💙 Relaciones (Flexibles)")
                    if not df_deudas.empty:
                        flexibles = df_deudas[df_deudas['tipo_deuda'] == 'Flexible']
                        if not flexibles.empty:
                            st.write("Sugerencia Bola de Nieve: Liquidar la deuda familiar más pequeña.")
                            if st.button("Abonar a Deuda Flexible"):
                                st.success("Acción registrada.")
                        else:
                            st.write("No hay deudas flexibles.")
                            
                with col_b:
                    st.markdown("### ❤️ Bancos (Avalancha)")
                    st.write("Inyección a capital bancario (Requiere mínimo 2 cuotas).")
                    if st.button("Abonar a Capital Bancario"):
                        st.success("Acción registrada.")
                        
                with col_c:
                    st.markdown("### 💚 Fondo / Inversión")
                    st.write("Costo de oportunidad: Ganar intereses en Plazo Fijo.")
                    if st.button(f"Enviar S/ {saldo_disponible:.2f} a Ahorro"):
                        conn = conectar_bd()
                        cur = conn.cursor()
                        cur.execute("INSERT INTO movimientos (tipo, categoria, monto, fecha, periodo, descripcion) VALUES (%s, %s, %s, %s, %s, %s)",
                                    ("Ahorro", "Fondo de Emergencia", saldo_disponible, f"{mes_seleccionado}-01", mes_seleccionado, "Traspaso a Ahorro/Inversión"))
                        conn.commit()
                        cur.close()
                        conn.close()
                        st.success("¡Traspaso registrado con éxito!")
                        st.rerun()

# --- 3. REGISTRAR MOVIMIENTO ---
elif accion == "Registrar Movimiento":
    st.subheader("📝 Agregar Nuevo Movimiento a la Nube")
    with st.form("form_movimiento"):
        tipo = st.selectbox("Tipo de Movimiento", ["Gasto", "Ingreso", "Ahorro"])
        categoria = st.selectbox("Categoría", CATEGORIAS_INGRESOS_BASE if tipo == "Ingreso" else (CATEGORIAS_AHORRO if tipo == "Ahorro" else CATEGORIAS_GASTOS))
        monto = st.number_input("Monto (S/)", min_value=0.0, format="%.2f")
        fecha = st.date_input("Fecha de Operación", value=datetime.now())
        descripcion = st.text_input("Descripción (Ej: Yape pollo en el mercado)")
        
        if st.form_submit_button("Guardar en Neon"):
            fecha_str = fecha.strftime("%Y-%m-%d")
            periodo_calc = obtener_periodo(fecha_str)
            conn = conectar_bd()
            cur = conn.cursor()
            cur.execute("INSERT INTO movimientos (tipo, categoria, monto, fecha, periodo, descripcion) VALUES (%s, %s, %s, %s, %s, %s)",
                        (tipo, categoria, monto, fecha_str, periodo_calc, descripcion))
            conn.commit()
            cur.close()
            conn.close()
            st.success("¡Movimiento guardado en la nube!")
            st.rerun()

# --- 4. ESTADO DE DEUDAS ---
elif accion == "Estado de Deudas":
    st.subheader("💳 Estado de Deudas y Préstamos")
    conn = conectar_bd()
    df_deudas = pd.read_sql("SELECT * FROM deudas", conn)
    conn.close()
    
    if not df_deudas.empty:
        st.dataframe(df_deudas, use_container_width=True)
    else:
        st.info("No hay deudas configuradas aún.")