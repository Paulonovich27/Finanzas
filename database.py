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

def cargar_movimientos():
    conn = conectar_bd()
    df = pd.read_sql("SELECT id, tipo, categoria, monto, fecha, periodo, descripcion FROM movimientos ORDER BY fecha DESC", conn)
    conn.close()
    return df