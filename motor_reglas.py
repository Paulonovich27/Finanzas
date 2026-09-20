# motor_reglas.py

def aplicar_reglas(desc_raw, monto_absoluto, tipo_inicial):
    desc_upper = desc_raw.upper()
    tipo = tipo_inicial
    categoria = "Otros Gastos" if tipo == "Gasto" else "Otros Ingresos"
    desc_final = desc_raw
    
    # 1. Servicios
    if "TELE000991200249" in desc_upper: categoria = "Celular Fiorella"
    elif "CLAR000046603204" in desc_upper: categoria = "Internet" if monto_absoluto > 100 else "Celular Paul"
    elif "PLUZ000003243243" in desc_upper: categoria = "Luz"
    elif "CALI000001613701" in desc_upper: categoria = "Gas Pa"
    elif "CALI000005926001" in desc_upper: categoria = "Gas Paul"
    
    # 2. Entretenimiento y Juegos
    elif "YOUTUBE" in desc_upper: categoria, desc_final = "Otros Gastos", "Youtube"
    elif "NETFLIX" in desc_upper: categoria, desc_final = "Otros Gastos", "Netflix"
    elif "ROBLOX" in desc_upper: categoria, desc_final = "Otros Gastos", "Roblox"
    elif "MINECRAFT" in desc_upper: categoria, desc_final = "Otros Gastos", "Minecraft"
    elif any(x in desc_upper for x in ["TOCA BOCA", "EA MOBILE", "USTWO GAMES", "LOADCOMPLET", "GAMING"]): categoria, desc_final = "Otros Gastos", "Otros juegos"
    elif "CINEPLANET" in desc_upper or "CINEMARK" in desc_upper: categoria, desc_final = "Otros Gastos", "Cine"
    elif "MR JOY" in desc_upper: categoria, desc_final = "Otros Gastos", "Mall"
    
    # 3. Compras, Supermercados, Farmacia y Tiendas
    elif "PLAZA VE" in desc_upper or "ECONOMAX" in desc_upper: categoria = "Supermercado"
    elif "PROMART" in desc_upper or "CASAIDEAS" in desc_upper: categoria, desc_final = "Otros Gastos", "Cosas de casa"
    elif "TAI LOY" in desc_upper: categoria, desc_final = "Otros Gastos", "Cosas de colegio"
    elif "SIFRAH" in desc_upper: categoria, desc_final = "Otros Gastos", "Cosas varias"
    elif "TEMU" in desc_upper: categoria, desc_final = "Otros Gastos", "TEMU"
    elif "RIPLEY" in desc_upper: categoria, desc_final = "Otros Gastos", "Ropa"
    elif "IKF" in desc_upper or "BOTICA" in desc_upper: categoria, desc_final = "Otros Gastos", "Medicina"
    elif "LURIGANCHO C9" in desc_upper or "RUISENORES C10" in desc_upper: categoria, desc_final = "Otros Gastos", "TAMBO"
    elif "FALABELLA" in desc_upper: categoria, desc_final = "Otros Gastos", "Fallabella"
    
    # 4. Comida y Restaurantes
    elif any(x in desc_upper for x in ["KFC", "FRUTIX", "UMARI", "SAN MARCELO", "DON FANO", "DINOLAN"]): categoria, desc_final = "Comida", "Fast Food"
    elif "DAMIANA VIL" in desc_upper: categoria, desc_final = "Comida", "Mercado Lonchera"
    elif "MARIA QUI" in desc_upper: categoria, desc_final = "Comida", "Mercado verdura"
    elif "CARMEN CON" in desc_upper: categoria, desc_final = "Comida", "Mercado fruta"
    elif "JOSE ORT" in desc_upper or "LUZ MAS" in desc_upper: categoria, desc_final = "Comida", "Mercado abarrotes"
    
    # 5. Seguros, Colegios, Retiros y Bancos
    elif "KASH00PSJE051702" in desc_upper: categoria = "Mantenimiento + agua"
    elif "HIJO000090911511" in desc_upper: categoria = "Colegio Joanne"
    elif "HIJO000079578900" in desc_upper: categoria = "Colegio Joaquin"
    elif "MAPFRE" in desc_upper or "MAPF0" in desc_upper: categoria, desc_final = "Mapfre", "Pago Mapfre"
    elif "SEG.MI" in desc_upper or "SEG MI" in desc_upper: categoria, desc_final = "Otros Gastos", "Seguro BBVA"
    elif "PAGO CRED YAPE" in desc_upper: categoria, desc_final = "Otros Gastos", "Pago de prestamo yape"
    elif "CREDITO YAPE" in desc_upper: tipo, categoria = "Ingreso", "Prestamo Yape"
    elif "RETIRO EFECTIVO" in desc_upper or "RETIRO AG" in desc_upper or "RET. GLOBALNET" in desc_upper or "USO DEL CAJERO" in desc_upper: 
        categoria, desc_final = "Otros Gastos", "Retiro de efectivo"
    elif "MANT. CUENTA" in desc_upper or "IMPUESTO ITF" in desc_upper: categoria = "Intereses"
    elif "TRANSF.FIN.OH" in desc_upper: categoria, desc_final = "Otros Gastos", "OH"
    elif "ABONO MARTIN PAUL" in desc_upper: tipo, categoria, desc_final = "Ingreso", "Otros Ingresos", "Intereses"
    elif "DE OTRA CUENTA" in desc_upper or "DEPOSITO EFECTIVO" in desc_upper: pass
        
    # Préstamos BBVA (Inteligencia de montos)
    elif "P.P." in desc_upper or "P.P :" in desc_upper:
        if monto_absoluto > 2000:
            categoria, desc_final = "Hipoteca", "Pago Hipoteca"
        else:
            categoria, desc_final = "Prestamo personal (banco)", "Pago prestamo BBVA"

    # 6. Personas y Tesorería
    elif "FIORELLA BAL" in desc_upper:
        if tipo == "Gasto": categoria = "Otros Gastos"
        else: tipo, categoria, desc_final = "Ingreso", "Sueldo Esposa", "Sueldo Esposa"
    elif "MILAGRO MON" in desc_upper: categoria, desc_final = "Otros Gastos", "Deporte"
    elif any(x in desc_upper for x in ["SADITH ARZ", "ANTONIO PIC", "ELIZABETH JAC", "CAGNEY GUZ", "YESENIA GAR", "TERESA CAS", "LISBETH QUI", "ROSA POL", "NATALIA MOG", "ZAIDA DEL", "MARGOT CON", "LILIANA RAM", "JENNIFER HUA", "KATHERINE FER", "MEYLING", "GLADYS Q"]):
        categoria = "Otros Ingresos" if tipo == "Ingreso" else "Otros Gastos"
        desc_final = "Tesorero HMA"
        
    # 7. Transferencias Internas (Banbif, BBVA y BCP)
    elif any(x in desc_upper for x in ["MARTIN PAUL", "MARTIN P", "TRANSF.BCO", "TRAN.CTAS.TERC", "I/T-", " /T-", "FF YAPE-MARTIN"]):
        if "ABONO" not in desc_upper:
            categoria, desc_final = "Transferencia Interna", "Movimiento entre cuentas"
            
    # 8. Yapes Anónimos Banbif
    elif "TRF.INMED.CEL" in desc_upper or "TRF-INMED.CEL" in desc_upper or "TRANSF.RECIB" in desc_upper:
        if monto_absoluto == 500:
            categoria, desc_final = "Transferencia Interna", "Movimiento entre cuentas"
        else:
            categoria, desc_final = ("Otros Ingresos" if tipo == "Ingreso" else "Otros Gastos"), "YAPE/PLIN"
            
    # 9. Regla General para abonos desconocidos
    elif tipo == "Ingreso" and ("YAPE DE" in desc_upper or "ABON" in desc_upper):
        categoria, desc_final = "Otros Ingresos", f"Tesorero HMA (Revisar: {desc_raw})"
        
    return tipo, categoria, desc_final