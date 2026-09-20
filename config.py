# config.py
from datetime import datetime

DIA_CORTE = 25

CATEGORIAS_INGRESOS_BASE = ["Sueldo", "Sueldo Esposa", "Ayuda Papá (Colegio)", "Otros Ingresos"]
CATEGORIAS_GASTOS = [
    "Hipoteca", "Mantenimiento + agua", "Luz", "Gas Pa", "Gas Paul",
    "Internet", "Celular Paul", "Celular Fiorella", "Colegio Joanne", "Colegio Joaquin",
    "Comida", "Supermercado", "Mercado", "Pasajes Paul", "Pasajes Fiorella",
    "Mapfre", "Prestamo personal (banco)", "Prestamo Yape", "Mapfre deuda",
    "Prestamo Makoto", "Prestamo Mamá", "Prestamo Hijos", "Otros Gastos"
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