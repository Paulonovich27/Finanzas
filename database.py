# database.py
import streamlit as st
import psycopg2
import pandas as pd

def conectar_bd():
    try:
        conexion = psycopg2.connect(st.secrets["NEON_URL"])
        return conexion
    except Exception as e:
        st.error(f"Error al conectar con Neon: {e}")
        st.stop()

def inicializar_tablas():
    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id SERIAL PRIMARY KEY,
            tipo VARCHAR(50),
            categoria VARCHAR(100),
            monto NUMERIC(10, 2),
            fecha DATE,
            periodo VARCHAR(7),
            descripcion TEXT
        )
    """)
    
    # Agregamos la columna 'origen' de forma segura por si no existe
    cur.execute("ALTER TABLE movimientos ADD COLUMN IF NOT EXISTS origen VARCHAR(200) DEFAULT 'Manual';")
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS deudas (
            categoria VARCHAR(50) PRIMARY KEY,
            tipo_deuda VARCHAR(50),
            monto_original NUMERIC(10, 2),
            capital_pendiente NUMERIC(10, 2),
            cuota_total INT,
            cuota_actual INT,
            pago_mensual NUMERIC(10, 2)
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def cargar_movimientos():
    conn = conectar_bd()
    cur = conn.cursor()
    # Ahora también llamamos a la columna 'origen'
    cur.execute("SELECT id, tipo, categoria, monto, fecha, periodo, descripcion, origen FROM movimientos ORDER BY fecha DESC")
    columnas = [desc[0] for desc in cur.description]
    datos = cur.fetchall()
    df = pd.DataFrame(datos, columns=columnas)
    cur.close()
    conn.close()
    return df