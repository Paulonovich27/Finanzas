import sqlite3
import psycopg2

# 1. Conexión a tu SQLite local actual
sqlite_conn = sqlite3.connect("mis_finanzas.db")
sqlite_cursor = sqlite_conn.cursor()

# 2. Conexión a tu base de datos en Neon (PostgreSQL)
NEON_URL = "postgresql://neondb_owner:npg_oXkt6NJZPr5S@ep-crimson-frog-b4mm4qjn-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
neon_conn = psycopg2.connect(NEON_URL)
neon_cursor = neon_conn.cursor()

# 3. Crear las tablas en Neon si no existen
neon_cursor.execute('''
    CREATE TABLE IF NOT EXISTS movimientos (
        id SERIAL PRIMARY KEY,
        tipo TEXT, 
        categoria TEXT, 
        monto REAL, 
        fecha TEXT, 
        periodo TEXT, 
        descripcion TEXT
    )
''')

neon_cursor.execute('''
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
neon_conn.commit()

# 4. Migrar Movimientos
sqlite_cursor.execute("SELECT tipo, categoria, monto, fecha, periodo, descripcion FROM movimientos")
movimientos = sqlite_cursor.fetchall()

for mov in movimientos:
    neon_cursor.execute('''
        INSERT INTO movimientos (tipo, categoria, monto, fecha, periodo, descripcion)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', mov)

# 5. Migrar Deudas (si las tienes creadas)
try:
    sqlite_cursor.execute("SELECT categoria, tipo_deuda, monto_original, capital_pendiente, cuota_total, cuota_actual, pago_mensual FROM deudas")
    deudas = sqlite_cursor.fetchall()
    for deuda in deudas:
        neon_cursor.execute('''
            INSERT INTO deudas (categoria, tipo_deuda, monto_original, capital_pendiente, cuota_total, cuota_actual, pago_mensual)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (categoria) DO NOTHING
        ''', deuda)
except sqlite3.OperationalError:
    pass # Si la tabla deudas no existía localmente, no pasa nada

neon_conn.commit()
sqlite_conn.close()
neon_conn.close()

print("¡Migración completada con éxito a Neon!")