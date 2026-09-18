import sqlite3
import customtkinter as ctk
from datetime import datetime
import calendar
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- REGLA DE NEGOCIO: DÍA DE CORTE ---
DIA_CORTE = 25

CATEGORIAS_INGRESOS_BASE = [
    "Sueldo", "Sueldo Esposa", "Ayuda Papá (Colegio)", "Otros Ingresos"
]

CATEGORIAS_GASTOS = [
    "Hipoteca", "Mantenimiento + agua", "Luz", "Gas Pa", "Gas Paul",
    "Internet", "Celular Paul", "Celular Fiorella", "Colegio Joanne", "Colegio Joaquin",
    "Comida", "Supermercado", "Mercado", "Pasajes Paul", "Pasajes Fiorella",
    "Mapfre", "Prestamo personal (banco)", "Prestamo Yape", "Mapfre deuda",
    "Prestamo Makoto", "Prestamo Mamá", "Prestamo Hijos"
]

CATEGORIAS_AHORRO = [
    "Fondo de Emergencia", "Plazo Fijo", "Caja de Ahorros", "Inversiones"
]

DEUDAS_CATEGORIAS = [
    "Hipoteca", "Prestamo personal (banco)", "Prestamo Yape", "Mapfre deuda",
    "Prestamo Makoto", "Prestamo Mamá", "Prestamo Hijos"
]

def obtener_periodo(fecha_texto):
    try:
        dt = datetime.strptime(fecha_texto, "%Y-%m-%d")
        if dt.day >= DIA_CORTE:
            if dt.month == 12:
                return f"{dt.year + 1}-01"
            else:
                return f"{dt.year}-{dt.month + 1:02d}"
        else:
            return f"{dt.year}-{dt.month:02d}"
    except:
        return fecha_texto[:7]

def conectar_bd():
    conexion = sqlite3.connect("mis_finanzas.db")
    cursor = conexion.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT, categoria TEXT, monto REAL, fecha TEXT, periodo TEXT, descripcion TEXT
        )
    ''')
    cursor.execute('''
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
    
    cursor.execute("PRAGMA table_info(movimientos)")
    columnas = [col[1] for col in cursor.fetchall()]
    if 'periodo' not in columnas:
        cursor.execute("ALTER TABLE movimientos ADD COLUMN periodo TEXT")
        cursor.execute("SELECT id, fecha FROM movimientos")
        for row in cursor.fetchall():
            id_mov = row[0]
            fecha_real = row[1]
            periodo_correcto = obtener_periodo(fecha_real)
            cursor.execute("UPDATE movimientos SET periodo = ? WHERE id = ?", (periodo_correcto, id_mov))

    cursor.execute("UPDATE movimientos SET tipo = 'Ahorro', categoria = 'Fondo de Emergencia' WHERE categoria = 'Fondo de Emergencia / Inversión'")
            
    conexion.commit()
    return conexion

def obtener_ultimo_dia_mes():
    hoy = datetime.now()
    ultimo_dia = calendar.monthrange(hoy.year, hoy.month)[1]
    return f"{hoy.year}-{hoy.month:02d}-{ultimo_dia:02d}"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AppFinanzas(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Mi Gestor Financiero")
        self.geometry("1050x650")
        self.conexion = conectar_bd()
        
        self.frame_superior = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_superior.pack(pady=15, fill="x", padx=20)
        
        self.label_titulo = ctk.CTkLabel(self.frame_superior, text="Resumen de mis Finanzas", font=ctk.CTkFont(size=24, weight="bold"))
        self.label_titulo.pack(side="left")
        
        self.combo_mes = ctk.CTkOptionMenu(self.frame_superior, values=["Todos los meses"], command=self.cargar_datos)
        self.combo_mes.pack(side="left", padx=20)
        
        self.boton_predictor = ctk.CTkButton(self.frame_superior, text="💡 Predictor", command=self.abrir_predictor, fg_color="#F39C12", hover_color="#D68910")
        self.boton_predictor.pack(side="right", padx=5)

        self.boton_agregar = ctk.CTkButton(self.frame_superior, text="+ Movimiento", command=self.abrir_formulario)
        self.boton_agregar.pack(side="right", padx=5)
        
        self.boton_grafico = ctk.CTkButton(self.frame_superior, text="Gráfico", command=self.mostrar_grafico, fg_color="#8E44AD", hover_color="#732D91")
        self.boton_grafico.pack(side="right", padx=5)

        self.boton_deudas = ctk.CTkButton(self.frame_superior, text="Deudas", command=self.abrir_ventana_deudas, fg_color="#D35400", hover_color="#A04000")
        self.boton_deudas.pack(side="right", padx=5)

        self.frame_resumen = ctk.CTkFrame(self)
        self.frame_resumen.pack(pady=5, padx=20, fill="x")
        
        self.lbl_total_ingresos = ctk.CTkLabel(self.frame_resumen, text="Ingresos: S/ 0.00", font=ctk.CTkFont(size=16, weight="bold"), text_color="#2ECC71")
        self.lbl_total_ingresos.pack(side="left", expand=True, pady=15)
        self.lbl_total_gastos = ctk.CTkLabel(self.frame_resumen, text="Gastos: S/ 0.00", font=ctk.CTkFont(size=16, weight="bold"), text_color="#E74C3C")
        self.lbl_total_gastos.pack(side="left", expand=True, pady=15)
        self.lbl_total_ahorros = ctk.CTkLabel(self.frame_resumen, text="Ahorros: S/ 0.00", font=ctk.CTkFont(size=16, weight="bold"), text_color="#3498DB")
        self.lbl_total_ahorros.pack(side="left", expand=True, pady=15)
        self.lbl_saldo = ctk.CTkLabel(self.frame_resumen, text="Saldo: S/ 0.00", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
        self.lbl_saldo.pack(side="left", expand=True, pady=15)

        self.frame_lista = ctk.CTkScrollableFrame(self, width=900, height=350)
        self.frame_lista.pack(pady=10, padx=20, fill="both", expand=True)
        
        self.cargar_datos()

    def cargar_datos(self, mes_seleccionado=None):
        cursor = self.conexion.cursor()
        
        cursor.execute("SELECT DISTINCT periodo FROM movimientos WHERE periodo IS NOT NULL ORDER BY periodo DESC")
        meses_db = cursor.fetchall()
        opciones_meses = ["Todos los meses"] + [m[0] for m in meses_db if m[0]]
        self.combo_mes.configure(values=opciones_meses)
        
        mes_actual = self.combo_mes.get()
        if mes_actual not in opciones_meses:
            mes_actual = "Todos los meses"
            self.combo_mes.set(mes_actual)

        for widget in self.frame_lista.winfo_children():
            widget.destroy()
            
        if mes_actual == "Todos los meses":
            cursor.execute("SELECT id, tipo, categoria, monto, fecha, periodo, descripcion FROM movimientos ORDER BY periodo DESC, fecha DESC")
        else:
            cursor.execute("SELECT id, tipo, categoria, monto, fecha, periodo, descripcion FROM movimientos WHERE periodo = ? ORDER BY fecha DESC", (mes_actual,))
            
        filas = cursor.fetchall()
        suma_ingresos, suma_gastos, suma_ahorros = 0.0, 0.0, 0.0
        
        encabezado = ctk.CTkFrame(self.frame_lista, fg_color="transparent")
        encabezado.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(encabezado, text="Fecha [Flujo]", width=110, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(encabezado, text="Tipo", width=70, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(encabezado, text="Categoría", width=180, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(encabezado, text="Descripción", width=220, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(encabezado, text="Monto", width=90, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        
        for fila in filas:
            if len(fila) == 7:
                id_mov, tipo, categoria, monto, fecha, periodo, descripcion = fila
            else:
                id_mov, tipo, categoria, monto, fecha, periodo = fila
                descripcion = ""

            fecha_corta = fecha.split(" ")[0] 
            texto_fecha = f"{fecha_corta} [{periodo}]"
            
            item_frame = ctk.CTkFrame(self.frame_lista, fg_color="transparent", corner_radius=5)
            item_frame.pack(fill="x", pady=2, ipadx=5, ipady=2)
            
            if tipo == "Ingreso":
                color_monto, signo = "#2ECC71", "+"
                suma_ingresos += monto
            elif tipo == "Ahorro":
                color_monto, signo = "#3498DB", "-"
                suma_ahorros += monto
            else:
                color_monto, signo = "#E74C3C", "-"
                suma_gastos += monto
            
            lbl_f = ctk.CTkLabel(item_frame, text=texto_fecha, width=110, anchor="w")
            lbl_f.pack(side="left", padx=5)
            lbl_t = ctk.CTkLabel(item_frame, text=tipo, width=70, anchor="w")
            lbl_t.pack(side="left", padx=5)
            lbl_c = ctk.CTkLabel(item_frame, text=categoria, width=180, anchor="w")
            lbl_c.pack(side="left", padx=5)
            
            desc_mostrar = descripcion if descripcion else "-"
            if len(desc_mostrar) > 25: desc_mostrar = desc_mostrar[:22] + "..."
            lbl_d = ctk.CTkLabel(item_frame, text=desc_mostrar, width=220, anchor="w", text_color="gray")
            lbl_d.pack(side="left", padx=5)
            
            lbl_m = ctk.CTkLabel(item_frame, text=f"{signo} S/ {monto:.2f}", width=90, anchor="w", text_color=color_monto, font=ctk.CTkFont(weight="bold"))
            lbl_m.pack(side="left", padx=5)
            
            btn_x = ctk.CTkButton(item_frame, text="X", width=30, fg_color="#C0392B", hover_color="#922B21", command=lambda i=id_mov: self.confirmar_eliminar(i))
            btn_x.pack(side="right", padx=5)
            btn_e = ctk.CTkButton(item_frame, text="Editar", width=60, fg_color="#F39C12", hover_color="#D68910", command=lambda i=id_mov: self.abrir_formulario(i))
            btn_e.pack(side="right", padx=5)

            color_fondo = item_frame.cget("fg_color")
            color_hover = "#2C3E50"
            
            def on_enter(e, frame=item_frame): frame.configure(fg_color=color_hover)
            def on_leave(e, frame=item_frame): frame.configure(fg_color=color_fondo)

            item_frame.bind("<Enter>", on_enter)
            item_frame.bind("<Leave>", on_leave)
            for widget in [lbl_f, lbl_t, lbl_c, lbl_d, lbl_m]:
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)

        self.lbl_total_ingresos.configure(text=f"Ingresos: S/ {suma_ingresos:.2f}")
        self.lbl_total_gastos.configure(text=f"Gastos: S/ {suma_gastos:.2f}")
        self.lbl_total_ahorros.configure(text=f"Ahorros: S/ {suma_ahorros:.2f}")
        self.lbl_saldo.configure(text=f"Saldo: S/ {(suma_ingresos - suma_gastos - suma_ahorros):.2f}")

    def confirmar_eliminar(self, id_mov):
        dialogo = ctk.CTkToplevel(self)
        dialogo.title("Confirmar acción")
        dialogo.geometry("350x150")
        dialogo.grab_set()

        ctk.CTkLabel(dialogo, text="¿Estás seguro de eliminar este registro?", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=20)
        
        frame_btns = ctk.CTkFrame(dialogo, fg_color="transparent")
        frame_btns.pack(fill="x", pady=10)

        def ejecutar_borrado():
            cursor = self.conexion.cursor()
            cursor.execute("DELETE FROM movimientos WHERE id=?", (id_mov,))
            self.conexion.commit()
            self.cargar_datos()
            dialogo.destroy()

        ctk.CTkButton(frame_btns, text="Sí, Eliminar", fg_color="#C0392B", hover_color="#922B21", width=120, command=ejecutar_borrado).pack(side="left", padx=20)
        ctk.CTkButton(frame_btns, text="Cancelar", fg_color="gray", hover_color="darkgray", width=120, command=dialogo.destroy).pack(side="right", padx=20)

    def eliminar_movimiento(self, id_mov):
        pass

    def mostrar_grafico(self):
        cursor = self.conexion.cursor()
        mes_actual = self.combo_mes.get()
        
        if mes_actual == "Todos los meses":
            cursor.execute("SELECT categoria, SUM(monto) FROM movimientos WHERE tipo='Gasto' GROUP BY categoria")
        else:
            cursor.execute("SELECT categoria, SUM(monto) FROM movimientos WHERE tipo='Gasto' AND periodo = ? GROUP BY categoria", (mes_actual,))
            
        datos = cursor.fetchall()
        if not datos:
            return
        
        categorias = [fila[0] for fila in datos]
        montos = [fila[1] for fila in datos]
        ventana_grafico = ctk.CTkToplevel(self)
        ventana_grafico.title(f"Distribución de Gastos ({mes_actual})")
        ventana_grafico.geometry("700x550")
        
        ctk.CTkLabel(ventana_grafico, text=f"Distribución de Gastos ({mes_actual})", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        fig, ax = plt.subplots(figsize=(7, 5))
        fig.patch.set_facecolor('#242424') 
        ax.set_facecolor('#242424')
        ax.pie(montos, labels=categorias, autopct='%1.1f%%', startangle=140, textprops=dict(color="white", fontsize=9))
        canvas = FigureCanvasTkAgg(fig, master=ventana_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)

    # --- LÓGICA DEL PREDICTOR AVANZADO (CON ALERTA DE SUPERVIVENCIA) ---
    def abrir_predictor(self):
        mes_actual = self.combo_mes.get()
        
        if mes_actual == "Todos los meses":
            ventana_error = ctk.CTkToplevel(self)
            ventana_error.title("Aviso del Predictor")
            ventana_error.geometry("450x200")
            ventana_error.grab_set()
            ctk.CTkLabel(ventana_error, text="⚠️ Selecciona un mes específico", font=ctk.CTkFont(size=18, weight="bold"), text_color="#F39C12").pack(pady=(30, 10))
            ctk.CTkLabel(ventana_error, text="El Predictor analiza escenarios reales.\nSelecciona el mes donde quieres predecir tu excedente.").pack()
            ctk.CTkButton(ventana_error, text="Entendido", command=ventana_error.destroy).pack(pady=20)
            return

        ventana = ctk.CTkToplevel(self)
        ventana.title(f"Inteligencia Financiera - Flujo {mes_actual}")
        ventana.geometry("1000x600") # Aumentado para dar espacio a la alerta si aparece
        ventana.grab_set()

        ctk.CTkLabel(ventana, text="Estrategia de Excedentes y Ahorro", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)

        cursor = self.conexion.cursor()
        
        # 1. CHEQUEO DE SUPERVIVENCIA (Comida / Supermercado / Mercado)
        cursor.execute("SELECT SUM(monto) FROM movimientos WHERE periodo = ? AND tipo = 'Gasto' AND categoria IN ('Comida', 'Supermercado', 'Mercado')", (mes_actual,))
        gasto_alimentos = cursor.fetchone()[0]
        if gasto_alimentos is None: gasto_alimentos = 0.0

        if gasto_alimentos == 0.0:
            marco_alerta_comida = ctk.CTkFrame(ventana, fg_color="#D35400") # Naranja oscuro alerta
            marco_alerta_comida.pack(pady=(0, 15), padx=30, fill="x")
            ctk.CTkLabel(marco_alerta_comida, text="⚠️ ALERTA DE FALSA LIQUIDEZ: FALTAN GASTOS ESENCIALES", font=ctk.CTkFont(weight="bold", size=14), text_color="white").pack(pady=(10, 2))
            texto_alerta = "No has registrado compras en Alimentación (Mercado/Supermercado) en este flujo mensual.\nTen cuidado: el saldo que ves abajo es engañoso. Reserva dinero para tu alimentación antes de abonar a deudas."
            ctk.CTkLabel(marco_alerta_comida, text=texto_alerta, font=ctk.CTkFont(size=12)).pack(pady=(0, 10))

        # 2. Cálculo de saldo disponible
        cursor.execute("SELECT tipo, monto FROM movimientos WHERE periodo = ?", (mes_actual,))
        filas = cursor.fetchall()
        ingresos = sum(f[1] for f in filas if f[0] == "Ingreso")
        gastos = sum(f[1] for f in filas if f[0] == "Gasto")
        ahorros_ya_hechos = sum(f[1] for f in filas if f[0] == "Ahorro")
        
        saldo_disponible = ingresos - gastos - ahorros_ya_hechos

        color_saldo = "#2ECC71" if saldo_disponible > 0 else "#E74C3C"
        ctk.CTkLabel(ventana, text=f"Saldo disponible proyectado:", font=ctk.CTkFont(size=14)).pack(pady=(5,0))
        ctk.CTkLabel(ventana, text=f"S/ {saldo_disponible:.2f}", font=ctk.CTkFont(size=26, weight="bold"), text_color=color_saldo).pack(pady=(0,10))

        if saldo_disponible <= 0:
            ctk.CTkLabel(ventana, text="No cuentas con liquidez proyectada este mes para realizar inversiones o pagar deudas extra.", text_color="gray").pack(pady=20)
            return

        def realizar_abono(categoria_destino, monto_abono, desc, tipo_movimiento="Gasto"):
            fecha_abono = f"{mes_actual}-01" 
            cursor.execute("INSERT INTO movimientos (tipo, categoria, monto, fecha, periodo, descripcion) VALUES (?, ?, ?, ?, ?, ?)", 
                           (tipo_movimiento, categoria_destino, monto_abono, fecha_abono, mes_actual, desc))
            self.conexion.commit()
            self.cargar_datos() 
            ventana.destroy()

        UMBRAL_MINIMO = 800.0

        if saldo_disponible < UMBRAL_MINIMO:
            marco_alerta = ctk.CTkFrame(ventana, fg_color="#1E8449")
            marco_alerta.pack(pady=20, padx=30, fill="both", expand=True)
            ctk.CTkLabel(marco_alerta, text="⚠️ Sugerencia: Prioriza tu Liquidez", font=ctk.CTkFont(size=18, weight="bold"), text_color="white").pack(pady=(20,10))
            explicacion = (
                f"Tienes un excedente de S/ {saldo_disponible:.2f}, pero al ser menor a S/ {UMBRAL_MINIMO:.0f}, la estrategia\n"
                f"más inteligente es NO tocarlo y enviarlo a tu Fondo de Emergencia.\n\n"
                f"Abonos pequeños no reducen tus deudas bancarias significativamente y te dejan vulnerable\n"
                f"ante imprevistos o gastos sorpresas del mes."
            )
            ctk.CTkLabel(marco_alerta, text=explicacion, font=ctk.CTkFont(size=14)).pack(pady=10)
            ctk.CTkButton(marco_alerta, text=f"Guardar S/ {saldo_disponible:.2f} como Ahorro", fg_color="#2ECC71", hover_color="#27AE60", font=ctk.CTkFont(weight="bold"), 
                          command=lambda: realizar_abono("Fondo de Emergencia", saldo_disponible, "Ahorro por seguridad", "Ahorro")).pack(pady=20)
            return

        cursor.execute("SELECT categoria, tipo_deuda, monto_original, capital_pendiente, pago_mensual FROM deudas")
        todas_deudas = cursor.fetchall()
        
        deudas_flexibles = []
        deuda_banco_max = None
        max_capital_banco = 0.0
        cuota_banco_max = 0.0

        for deuda in todas_deudas:
            categoria, tipo_deuda, m_orig, cap_pend, pago_mensual = deuda
            if tipo_deuda == "Flexible":
                cursor.execute("SELECT SUM(monto) FROM movimientos WHERE categoria=?", (categoria,))
                pagos_app = cursor.fetchone()[0] or 0.0
                faltante = m_orig - (cap_pend + pagos_app)
                if faltante > 0:
                    deudas_flexibles.append((categoria, faltante))
            elif tipo_deuda == "Bancario":
                if cap_pend > max_capital_banco:
                    max_capital_banco = cap_pend
                    deuda_banco_max = categoria
                    cuota_banco_max = pago_mensual

        marco_opciones = ctk.CTkFrame(ventana, fg_color="transparent")
        marco_opciones.pack(fill="both", expand=True, padx=10, pady=10)

        marco_a = ctk.CTkFrame(marco_opciones, fg_color="#1F618D", width=300)
        marco_a.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(marco_a, text="Relaciones (Flexibles)", font=ctk.CTkFont(size=16, weight="bold"), text_color="white").pack(pady=(15,5))
        
        if deudas_flexibles:
            deudas_flexibles.sort(key=lambda x: x[1]) 
            obj_flex = deudas_flexibles[0][0]
            faltante_flex = deudas_flexibles[0][1]
            monto_sug_flex = min(saldo_disponible, faltante_flex)
            texto_a = f"Prioriza liquidar deudas pequeñas.\n\nObjetivo: {obj_flex}\nFaltante: S/ {faltante_flex:.2f}"
            ctk.CTkLabel(marco_a, text=texto_a, font=ctk.CTkFont(size=13)).pack(pady=20)
            ctk.CTkButton(marco_a, text=f"Pagar S/ {monto_sug_flex:.2f}", fg_color="#2980B9", hover_color="#1A5276", 
                          command=lambda: realizar_abono(obj_flex, monto_sug_flex, "Abono Bola de Nieve", "Gasto")).pack(pady=15, side="bottom")
        else:
            ctk.CTkLabel(marco_a, text="\nSin deudas\nflexibles.", text_color="#F1C40F").pack(pady=30)

        marco_b = ctk.CTkFrame(marco_opciones, fg_color="#900C3F", width=300)
        marco_b.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(marco_b, text="Bancos (Avalancha)", font=ctk.CTkFont(size=16, weight="bold"), text_color="white").pack(pady=(15,5))

        if deuda_banco_max:
            minimo_banco = cuota_banco_max * 2
            if saldo_disponible >= minimo_banco:
                texto_b = f"Cumples el requisito de >2 cuotas\npara reducir intereses reales.\n\nObjetivo: {deuda_banco_max}\nAbono a Capital: S/ {saldo_disponible:.2f}"
                ctk.CTkLabel(marco_b, text=texto_b, font=ctk.CTkFont(size=13)).pack(pady=20)
                ctk.CTkButton(marco_b, text=f"Abonar S/ {saldo_disponible:.2f}", fg_color="#C70039", hover_color="#641E16", 
                              command=lambda: realizar_abono(deuda_banco_max, saldo_disponible, "Abono a Capital", "Gasto")).pack(pady=15, side="bottom")
            else:
                texto_b = f"Los bancos exigen mínimo 2 cuotas\n(Aprox. S/ {minimo_banco:.2f}) para hacer efectivo\nel abono.\n\nTu saldo no es suficiente."
                ctk.CTkLabel(marco_b, text=texto_b, text_color="gray", font=ctk.CTkFont(size=12)).pack(pady=20)
                btn_b = ctk.CTkButton(marco_b, text="Opción Bloqueada", state="disabled", fg_color="gray")
                btn_b.pack(pady=15, side="bottom")
        else:
            ctk.CTkLabel(marco_b, text="\nSin deudas\nbancarias.", text_color="#F1C40F").pack(pady=30)

        marco_c = ctk.CTkFrame(marco_opciones, fg_color="#1E8449", width=300)
        marco_c.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(marco_c, text="Fondo / Inversión", font=ctk.CTkFont(size=16, weight="bold"), text_color="white").pack(pady=(15,5))
        texto_c = f"El costo de oportunidad: A veces\nes mejor ganar intereses en un Plazo\nFijo que dárselo al banco hoy.\n\nFondo Seguro: S/ {saldo_disponible:.2f}"
        ctk.CTkLabel(marco_c, text=texto_c, font=ctk.CTkFont(size=13)).pack(pady=20)
        ctk.CTkButton(marco_c, text=f"Ahorrar S/ {saldo_disponible:.2f}", fg_color="#27AE60", hover_color="#1D8348", 
                      command=lambda: realizar_abono("Fondo de Emergencia", saldo_disponible, "Traspaso a Ahorro/Inversión", "Ahorro")).pack(pady=15, side="bottom")

    # --- VENTANA DE ESTADO DE DEUDAS (SIN CAMBIOS) ---
    def abrir_ventana_deudas(self):
        ventana = ctk.CTkToplevel(self)
        ventana.title("Estado de Deudas")
        ventana.geometry("1000x550") 
        ventana.grab_set()

        frame_top = ctk.CTkFrame(ventana, fg_color="transparent")
        frame_top.pack(pady=15, fill="x", padx=20)

        ctk.CTkLabel(frame_top, text="Progreso de Deudas y Préstamos", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        ctk.CTkButton(frame_top, text="Registrar Cuotas del Mes (Bancarias)", fg_color="#27AE60", hover_color="#1E8449", command=self.registrar_cuotas_automaticas).pack(side="right")

        marco_deudas = ctk.CTkScrollableFrame(ventana, width=950, height=400)
        marco_deudas.pack(pady=10, padx=20, fill="both", expand=True)

        cursor = self.conexion.cursor()

        for categoria in DEUDAS_CATEGORIAS:
            cursor.execute("SELECT tipo_deuda, monto_original, capital_pendiente, cuota_total, cuota_actual, pago_mensual FROM deudas WHERE categoria=?", (categoria,))
            meta_deuda = cursor.fetchone()
            
            cursor.execute("SELECT SUM(monto) FROM movimientos WHERE categoria=? AND tipo='Gasto'", (categoria,))
            pagos = cursor.fetchone()
            total_pagado_movimientos = pagos[0] if pagos[0] else 0.0

            item_frame = ctk.CTkFrame(marco_deudas)
            item_frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(item_frame, text=categoria, width=180, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=10)

            if meta_deuda:
                tipo_deuda, monto_original, cap_pendiente, cuota_total, cuota_actual, pago_mensual = meta_deuda
                
                if tipo_deuda == "Flexible":
                    pagos_previos = cap_pendiente
                    pago_total_acumulado = total_pagado_movimientos + pagos_previos
                    faltante = monto_original - pago_total_acumulado
                    texto_info = f"Prestado: S/{monto_original:.2f} | Pagado Total: S/{pago_total_acumulado:.2f} | Faltante: S/{faltante:.2f}"
                    ctk.CTkLabel(item_frame, text=texto_info, width=600, anchor="w", text_color="#F1C40F", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
                
                elif tipo_deuda == "Bancario":
                    texto_banco1 = f"Cap. Prestado: S/{monto_original:.2f} | Cap. Pendiente: S/{cap_pendiente:.2f}"
                    texto_banco2 = f"Cuota: {cuota_actual}/{cuota_total} | Mensual: S/{pago_mensual:.2f}"
                    ctk.CTkLabel(item_frame, text=texto_banco1, width=320, anchor="w", text_color="#AAB7B8").pack(side="left", padx=5)
                    ctk.CTkLabel(item_frame, text=texto_banco2, width=280, anchor="w", text_color="white", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
            else:
                ctk.CTkLabel(item_frame, text="No configurado", width=600, anchor="w", text_color="gray").pack(side="left", padx=10)

            ctk.CTkButton(item_frame, text="Configurar", width=80, command=lambda c=categoria: self.configurar_deuda(c, ventana)).pack(side="right", padx=10)

    def registrar_cuotas_automaticas(self):
        cursor = self.conexion.cursor()
        cursor.execute("SELECT categoria, pago_mensual FROM deudas WHERE tipo_deuda='Bancario' AND pago_mensual > 0")
        bancarias = cursor.fetchall()
        
        if not bancarias:
            return

        fecha_fin_mes = obtener_ultimo_dia_mes()
        periodo_calc = obtener_periodo(fecha_fin_mes)
        
        for deuda in bancarias:
            categoria_banco = deuda[0]
            monto_cuota = deuda[1]
            
            cursor.execute("SELECT id FROM movimientos WHERE categoria=? AND fecha=? AND tipo='Gasto'", (categoria_banco, fecha_fin_mes))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO movimientos (tipo, categoria, monto, fecha, periodo, descripcion) VALUES (?, ?, ?, ?, ?, ?)", 
                               ("Gasto", categoria_banco, monto_cuota, fecha_fin_mes, periodo_calc, "Cuota automática"))
                cursor.execute("UPDATE deudas SET cuota_actual = cuota_actual + 1 WHERE categoria=?", (categoria_banco,))
                
        self.conexion.commit()
        self.cargar_datos() 

    def configurar_deuda(self, categoria, ventana_padre):
        ventana = ctk.CTkToplevel(ventana_padre)
        ventana.title(f"Configurar {categoria}")
        ventana.geometry("450x550") 
        ventana.grab_set()

        ctk.CTkLabel(ventana, text=f"Configuración: {categoria}", font=ctk.CTkFont(weight="bold", size=16)).pack(pady=10)

        cursor = self.conexion.cursor()
        cursor.execute("SELECT tipo_deuda, monto_original, capital_pendiente, cuota_total, cuota_actual, pago_mensual FROM deudas WHERE categoria=?", (categoria,))
        datos_actuales = cursor.fetchone()

        def guardar_meta():
            cursor = self.conexion.cursor()
            pestaña_activa = tabview.get()
            try:
                if pestaña_activa == "Personal / Flexible":
                    m_orig = float(entry_flex_original.get() or 0)
                    m_previo = float(entry_flex_pagado.get() or 0)
                    cursor.execute("INSERT OR REPLACE INTO deudas (categoria, tipo_deuda, monto_original, capital_pendiente, cuota_total, cuota_actual, pago_mensual) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                   (categoria, "Flexible", m_orig, m_previo, 0, 0, 0))
                else:
                    m_prestado = float(entry_ban_prestado.get() or 0)
                    m_pend = float(entry_ban_pendiente.get() or 0)
                    c_total = int(entry_ban_cuotatotal.get() or 0)
                    c_act = int(entry_ban_cuotaactual.get() or 0)
                    p_mensual = float(entry_ban_mensualidad.get() or 0)
                    
                    cursor.execute("INSERT OR REPLACE INTO deudas (categoria, tipo_deuda, monto_original, capital_pendiente, cuota_total, cuota_actual, pago_mensual) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                   (categoria, "Bancario", m_prestado, m_pend, c_total, c_act, p_mensual))
                
                self.conexion.commit()
                ventana.destroy()
                ventana_padre.destroy() 
                self.abrir_ventana_deudas()
            except ValueError:
                pass

        boton_guardar = ctk.CTkButton(ventana, text="Guardar Configuración", command=guardar_meta, fg_color="#27AE60", hover_color="#1E8449", height=40)
        boton_guardar.pack(side="bottom", pady=20) 

        tabview = ctk.CTkTabview(ventana, width=400, height=350)
        tabview.pack(padx=20, pady=10, fill="both")
        
        tab_flex = tabview.add("Personal / Flexible")
        tab_ban = tabview.add("Bancario / Estricto")

        ctk.CTkLabel(tab_flex, text="Monto Original Prestado:").pack(pady=(15,2))
        entry_flex_original = ctk.CTkEntry(tab_flex)
        entry_flex_original.pack(pady=5)

        ctk.CTkLabel(tab_flex, text="Monto que YA LE PAGASTE (Histórico):").pack(pady=(15,2))
        entry_flex_pagado = ctk.CTkEntry(tab_flex)
        entry_flex_pagado.pack(pady=5)
        entry_flex_pagado.insert(0, "0.0")

        if datos_actuales and datos_actuales[0] == "Flexible":
            entry_flex_original.insert(0, str(datos_actuales[1]))
            entry_flex_pagado.delete(0, 'end')
            entry_flex_pagado.insert(0, str(datos_actuales[2])) 

        ctk.CTkLabel(tab_ban, text="Capital Prestado:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        entry_ban_prestado = ctk.CTkEntry(tab_ban, width=120)
        entry_ban_prestado.grid(row=0, column=1, padx=10, pady=10)

        ctk.CTkLabel(tab_ban, text="Capital Pendiente:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        entry_ban_pendiente = ctk.CTkEntry(tab_ban, width=120)
        entry_ban_pendiente.grid(row=1, column=1, padx=10, pady=10)

        ctk.CTkLabel(tab_ban, text="Cuota Total / Actual:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        frame_cuotas = ctk.CTkFrame(tab_ban, fg_color="transparent")
        frame_cuotas.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        
        entry_ban_cuotaactual = ctk.CTkEntry(frame_cuotas, width=50)
        entry_ban_cuotaactual.pack(side="left", padx=(0,5))
        ctk.CTkLabel(frame_cuotas, text="/").pack(side="left")
        
        entry_ban_cuotatotal = ctk.CTkEntry(frame_cuotas, width=50)
        entry_ban_cuotatotal.pack(side="left", padx=(5,0))

        ctk.CTkLabel(tab_ban, text="Pago Mensual:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        entry_ban_mensualidad = ctk.CTkEntry(tab_ban, width=120)
        entry_ban_mensualidad.grid(row=3, column=1, padx=10, pady=10)

        if datos_actuales and datos_actuales[0] == "Bancario":
            entry_ban_prestado.insert(0, str(datos_actuales[1]))    
            entry_ban_pendiente.insert(0, str(datos_actuales[2]))   
            entry_ban_cuotatotal.insert(0, str(datos_actuales[3]))  
            entry_ban_cuotaactual.insert(0, str(datos_actuales[4])) 
            entry_ban_mensualidad.insert(0, str(datos_actuales[5])) 
            tabview.set("Bancario / Estricto") 

    # --- FORMULARIO DE MOVIMIENTOS ---
    def abrir_formulario(self, id_mov_editar=None):
        ventana = ctk.CTkToplevel(self)
        ventana.title("Movimiento")
        ventana.geometry("420x600")
        ventana.grab_set()

        tipo_actual = "Gasto"
        categoria_actual = CATEGORIAS_GASTOS[0]
        monto_actual = ""
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        desc_actual = ""

        if id_mov_editar:
            cursor = self.conexion.cursor()
            cursor.execute("SELECT tipo, categoria, monto, fecha, descripcion FROM movimientos WHERE id=?", (id_mov_editar,))
            datos = cursor.fetchone()
            if datos:
                tipo_actual, categoria_actual, monto_actual, fecha_actual, desc_actual = datos
                fecha_actual = fecha_actual.split(" ")[0] 
                if desc_actual is None: desc_actual = ""
            titulo, texto_boton = "Editar Movimiento", "Actualizar Cambios"
        else:
            titulo, texto_boton = "Nuevo Movimiento", "Guardar Movimiento"

        ctk.CTkLabel(ventana, text=titulo, font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)

        ctk.CTkLabel(ventana, text="Fecha (AAAA-MM-DD):").pack(pady=(5, 0))
        entry_fecha = ctk.CTkEntry(ventana, placeholder_text="2026-09-01")
        entry_fecha.insert(0, fecha_actual)
        entry_fecha.pack(pady=5)

        combo_categoria = ctk.CTkOptionMenu(ventana, values=["Cargando..."])
        combo_tipo = ctk.CTkOptionMenu(ventana, values=["Ingreso", "Gasto", "Ahorro"])

        def actualizar_combos(event=None):
            fecha_str = entry_fecha.get()
            tipo_sel = combo_tipo.get()
            cat_sel = combo_categoria.get()

            if tipo_sel == "Ingreso":
                lista_valida = CATEGORIAS_INGRESOS_BASE.copy()
                try:
                    dt = datetime.strptime(fecha_str, "%Y-%m-%d")
                    mes, anio = dt.month, dt.year
                except ValueError:
                    mes, anio = datetime.now().month, datetime.now().year

                if anio <= 2026:
                    lista_valida.insert(2, "CTS")
                    lista_valida.insert(3, "CTS Esposa")
                if mes in [7, 12]:
                    lista_valida.append("Gratificación")
                    lista_valida.append("Gratificación Esposa")
                
                combo_categoria.configure(values=lista_valida)
                if cat_sel in lista_valida: combo_categoria.set(cat_sel)
                else: combo_categoria.set(lista_valida[0])
                
            elif tipo_sel == "Ahorro":
                combo_categoria.configure(values=CATEGORIAS_AHORRO)
                if cat_sel in CATEGORIAS_AHORRO: combo_categoria.set(cat_sel)
                else: combo_categoria.set(CATEGORIAS_AHORRO[0])
                
            else:
                combo_categoria.configure(values=CATEGORIAS_GASTOS)
                if cat_sel in CATEGORIAS_GASTOS: combo_categoria.set(cat_sel)
                else: combo_categoria.set(CATEGORIAS_GASTOS[0])

        ctk.CTkLabel(ventana, text="Tipo de movimiento:").pack(pady=(10, 0))
        combo_tipo.configure(command=actualizar_combos)
        combo_tipo.set(tipo_actual)
        combo_tipo.pack(pady=5)

        ctk.CTkLabel(ventana, text="Categoría:").pack(pady=(10, 0))
        combo_categoria.pack(pady=5)
        combo_categoria.set(categoria_actual)

        entry_fecha.bind("<KeyRelease>", actualizar_combos)
        actualizar_combos()

        ctk.CTkLabel(ventana, text="Descripción (Ej. Yape verduras):").pack(pady=(10, 0))
        entry_desc = ctk.CTkEntry(ventana, width=200)
        entry_desc.insert(0, desc_actual)
        entry_desc.pack(pady=5)

        ctk.CTkLabel(ventana, text="Monto (usa punto para decimales):").pack(pady=(10, 0))
        entry_monto = ctk.CTkEntry(ventana)
        if monto_actual != "":
            entry_monto.insert(0, str(monto_actual))
        entry_monto.pack(pady=5)

        def guardar_datos():
            try:
                monto = float(entry_monto.get())
                descripcion_texto = entry_desc.get()
                cursor = self.conexion.cursor()
                
                fecha_ingresada = entry_fecha.get()
                periodo_calc = obtener_periodo(fecha_ingresada)
                
                if id_mov_editar:
                    cursor.execute("UPDATE movimientos SET tipo=?, categoria=?, monto=?, fecha=?, periodo=?, descripcion=? WHERE id=?", 
                                   (combo_tipo.get(), combo_categoria.get(), monto, fecha_ingresada, periodo_calc, descripcion_texto, id_mov_editar))
                else:
                    cursor.execute("INSERT INTO movimientos (tipo, categoria, monto, fecha, periodo, descripcion) VALUES (?, ?, ?, ?, ?, ?)", 
                                   (combo_tipo.get(), combo_categoria.get(), monto, fecha_ingresada, periodo_calc, descripcion_texto))
                self.conexion.commit()
                self.cargar_datos()
                ventana.destroy() 
            except ValueError:
                pass

        ctk.CTkButton(ventana, text=texto_boton, command=guardar_datos, fg_color="green", hover_color="darkgreen").pack(pady=30)

if __name__ == "__main__":
    app = AppFinanzas()
    app.mainloop()