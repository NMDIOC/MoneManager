import streamlit as st
import json
import os
import pandas as pd
import base64
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Control Financiero y Metas", layout="wide")

DB_FILE = "finanzas_data.json"

# --- FUNCIONES DE ALMACENAMIENTO Y BACKUP ---
def cargar_datos():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return mofificar_datos_defecto()
    return mofificar_datos_defecto()

def mofificar_datos_defecto():
    return {"balance": 0.0, "history": [], "missions": []}

def guardar_datos(datos):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)
    st.session_state.datos = datos

def generar_backup_string(datos):
    json_str = json.dumps(datos, ensure_ascii=False)
    return base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

def restaurar_backup_string(backup_str):
    try:
        decoded_bytes = base64.b64decode(backup_str.encode("utf-8"))
        datos = json.loads(decoded_bytes.decode("utf-8"))
        if "balance" in datos and "history" in datos and "missions" in datos:
            return datos, True
    except Exception:
        pass
    return None, False

# Inicializar datos en la sesión
if "datos" not in st.session_state:
    st.session_state.datos = cargar_datos()

datos = st.session_state.datos

# --- INTERFAZ DE USUARIO ---
st.title("Sistema de Gestión Financiera y Metas")

# Sidebar: Balance Actual y Ajuste Directo / Backups
with st.sidebar:
    st.header("💰 Balance Global")
    st.metric(label="Saldo Disponible", value=f"${datos['balance']:.2f}")
    
    with st.expander("Ajustar saldo inicial directamente"):
        nuevo_saldo = st.number_input("Establecer nuevo saldo total:", min_value=0.0, value=datos['balance'], step=10.0)
        if st.button("Actualizar Saldo"):
            datos["balance"] = nuevo_saldo
            guardar_datos(datos)
            st.rerun()
            
    st.markdown("---")
    st.header("💾 Respaldo (Backup)")
    
    # Exportar
    backup_texto = generar_backup_string(datos)
    st.text_area("Copia este código de respaldo:", value=backup_texto, height=100)
    
    # Importar
    st.markdown("**Restaurar Datos**")
    backup_input = st.text_area("Pega aquí tu código de respaldo para recuperar tus datos:", height=100)
    if st.button("Restaurar Copia de Seguridad"):
        nuevos_datos, exito = restaurar_backup_string(backup_input)
        if exito:
            guardar_datos(nuevos_datos)
            st.success("Datos restaurados correctamente.")
            st.rerun()
        else:
            st.error("Código de respaldo inválido.")

# Cuerpo principal: 3 Columnas para Operaciones, Metas y Gráficos
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("🔄 Registrar Movimiento")
    tipo = st.radio("Tipo de transacción:", ["Depósito", "Retiro"])
    monto = st.number_input("Monto ($):", min_value=0.01, step=5.0, value=10.0)
    descripcion = st.text_input("Concepto / Descripción:", value="Ej. Venta de Asset")
    
    if st.button("Ejecutar Transacción"):
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if tipo == "Retiro" and monto > datos["balance"]:
            st.error("Fondos insuficientes para realizar este retiro.")
        else:
            if tipo == "Depósito":
                datos["balance"] += monto
            else:
                datos["balance"] -= monto
                
            # Registrar en historial
            datos["history"].append({
                "fecha": fecha_actual,
                "tipo": tipo,
                "monto": monto,
                "descripcion": descripcion
            })
            guardar_datos(datos)
            st.success(f"{tipo} registrado con éxito.")
            st.rerun()

    st.markdown("---")
    
    st.subheader("🎯 Configurar Misiones (Metas)")
    with st.form("form_mision"):
        nombre_mision = st.text_input("Nombre de la meta:", value="Mac Studio M4 Max")
        objetivo_mision = st.number_input("Monto objetivo ($):", min_value=1.0, step=100.0, value=2900.0)
        enviar_mision = st.form_submit_button("Añadir Meta")
        
        if enviar_mision and nombre_mision:
            datos["missions"].append({
                "nombre": nombre_mision,
                "objetivo": objetivo_mision
            })
            guardar_datos(datos)
            st.success(f"Meta '{nombre_mision}' añadida.")
            st.rerun()

with col2:
    st.subheader("📊 Progreso de Misiones")
    if datos["missions"]:
        for idx, mi in enumerate(datos["missions"]):
            progreso_porcentaje = min(datos["balance"] / mi["objetivo"], 1.0)
            st.markdown(f"**{mi['nombre']}** (Objetivo: ${mi['objetivo']:.2f})")
            st.progress(progreso_porcentaje)
            st.write(f"Progreso actual: {progreso_porcentaje * 100:.1f}% (${datos['balance']:.2f} de ${mi['objetivo']:.2f})")
            
            if st.button(f"Eliminar meta: {mi['nombre']}", key=f"del_{idx}"):
                datos["missions"].pop(idx)
                guardar_datos(datos)
                st.rerun()
    else:
        st.info("No tienes misiones configuradas actualmente.")

st.markdown("---")

# --- SECCIÓN DE HISTORIAL Y VISUALIZACIONES ---
st.subheader("📈 Historial de Transacciones y Métricas Visuales")

if datos["history"]:
    df = pd.DataFrame(datos["history"])
    
    # Calcular totales
    total_ganado = df[df["tipo"] == "Depósito"]["monto"].sum()
    total_gastado = df[df["tipo"] == "Retiro"]["monto"].sum()
    
    m1, m2 = st.columns(2)
    m1.metric("Total Ganado (Depósitos)", f"${total_ganado:.2f}")
    m2.metric("Total Gastado (Retiros)", f"${total_gastado:.2f}")
    
    # Generar Organizadores Visuales
    v1, v2 = st.columns([1, 1])
    
    with v1:
        st.markdown("**Comparativa: Total Ingresos vs Gastos**")
        df_resumen = pd.DataFrame({
            "Categoría": ["Ingresos", "Gastos"],
            "Total ($)": [total_ganado, total_gastado]
        }).set_index("Categoría")
        st.bar_chart(df_resumen)
        
    with v2:
        st.markdown("**Flujo de Movimientos Recientes**")
        # Invertir el dataframe para mostrar lo más reciente arriba en la tabla gráfica
        df_visual = df.copy()
        df_visual["Monto Ajustado"] = df_visual.apply(lambda row: row["monto"] if row["tipo"] == "Depósito" else -row["monto"], axis=1)
        st.line_chart(df_visual["Monto Ajustado"])
        
    # Tabla detallada
    st.markdown("**Registro Detallado**")
    st.dataframe(df.sort_index(ascending=False), use_container_width=True)
    
    if st.button("Limpiar Historial"):
        datos["history"] = []
        guardar_datos(datos)
        st.rerun()
else:
    st.info("Aún no se registran transacciones para generar estadísticas.")
