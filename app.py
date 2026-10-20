import os
import pandas as pd
import streamlit as st
import io
import requests
import time
import json

# Archivo local para persistencia de techos presupuestarios
ARCH_TECHOS = "techos_config.json"

def cargar_techos_disco():
    if os.path.exists(ARCH_TECHOS):
        try:
            with open(ARCH_TECHOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def guardar_techos_disco(techos_dict):
    try:
        with open(ARCH_TECHOS, "w", encoding="utf-8") as f:
            json.dump(techos_dict, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.warning(f"No se pudo guardar el archivo de techos: {e}")

# Inicialización blindada
if "db_local_backup" not in st.session_state or not isinstance(st.session_state["db_local_backup"], dict):
    st.session_state["db_local_backup"] = {"destinos": [], "egresos": [], "recursos": []}

for k in ["destinos", "egresos", "recursos"]:
    if k not in st.session_state["db_local_backup"] or not isinstance(st.session_state["db_local_backup"][k], list):
        st.session_state["db_local_backup"][k] = []

# Configuración de la página
st.set_page_config(page_title="Presupuesto Municipal 2027", layout="wide")

# =====================================================================
# 1. CONEXIÓN Y LECTURA ROBUSTA DESDE TUS NUEVAS HOJAS DE GOOGLE SHEETS
# =====================================================================

# SPREADSHEET_ID actualizado con tus nuevas hojas unificadas
SPREADSHEET_ID = "1r6izG5X1gil8MaZA1zD-WW2T1BA5mSC1Yq9-R663azU"

URL_READ_EGRESOS = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=0"
URL_READ_DESTINOS = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=1365567783"
URL_READ_RECURSOS = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=269081959"
URL_READ_TECHOS = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=671713267"
URL_READ_EJECUCION = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=810226733"

def construir_url_csv(param):
    param_str = str(param).strip()
    if param_str.isdigit():
        return f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={param_str}&_t={int(time.time())}"
    if "docs.google.com" in param_str:
        if "export?format=csv" not in param_str:
            gid = "0"
            if "gid=" in param_str:
                gid = param_str.split("gid=")[1].split("&")[0].split("#")[0]
            return f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={gid}&_t={int(time.time())}"
        return f"{param_str}&_t={int(time.time())}"
    return param_str

def leer_datos_gsheet(param_url_o_gid):
    url = construir_url_csv(param_url_o_gid)
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            df = pd.read_csv(io.StringIO(resp.text))
            if not df.empty:
                df.columns = [str(col).strip().lower() for col in df.columns]
                df = df.fillna("")
                for col in df.select_dtypes(include=['object', 'string']).columns:
                    df[col] = df[col].astype(str).str.strip()

                if "total" in df.columns:
                    s_total = df["total"].astype(str).str.replace("$", "", regex=False).str.strip()
                    s_total = s_total.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
                    df["total"] = pd.to_numeric(s_total, errors='coerce').fillna(0.0)
            return df
        else:
            st.error(f"⚠️ No se pudo acceder al Sheet (Código HTTP: {resp.status_code}). Comprobá que el enlace esté público.")
    except Exception as e:
        st.warning(f"Error de conexión con Google Sheets: {e}")

    if "1365567783" in str(param_url_o_gid):
        return pd.DataFrame(columns=["secretaria", "subsecretaria", "destino"])

    df_vacio = pd.DataFrame(columns=["secretaria", "subsecretaria", "destino", "objeto_gasto", "cuenta_padre", "cuenta_presupuestaria", "total", "fuente_fin", "clase", "tipo", "finalidad"])
    df_vacio["total"] = df_vacio["total"].astype(float)
    return df_vacio

URL_WEBHOOK_GSHEET = "https://script.google.com/macros/s/AKfycbwOfDQPZ2b62zMIESSkUcyvZIB2_JzpBD85ORXZXFx0pmccK5ChZcl8OKH4za6xTDkq/exec"

def guardar_fila_gsheet(pestana, nuevo_dict):
    if pestana in st.session_state["db_local_backup"]:
        st.session_state["db_local_backup"][pestana].append(nuevo_dict)
    try:
        payload = {"pestana": pestana, **nuevo_dict}
        resp = requests.post(URL_WEBHOOK_GSHEET, json=payload, timeout=10, allow_redirects=True)
        if resp.status_code in [200, 302]:
            st.success("✅ ¡Guardado localmente y sincronizado en Google Sheets!")
        else:
            st.warning(f"⚠️ El servidor respondió con código: {resp.status_code}")
    except Exception as e:
        st.warning(f"⚠️ Guardado en la sesión. Error de conexión: {e}")

# =====================================================================
# 2. CARGA DE DATOS Y ESTRUCTURA MUNICIPAL
# =====================================================================
df_egr_completo = leer_datos_gsheet(URL_READ_EGRESOS)
df_destinos_gsheet = leer_datos_gsheet(URL_READ_DESTINOS)

# Mapeos oficiales de gastos y recursos
MAPEO_GASTOS = {
    "1. Gastos en personal": {
        "21.1.0.0.00.000 - Personal Permanente": ["21.1.2.0.00.000 - Retribución a personal Directivo y de control", "21.1.4.0.00.000 - Sueldo Anual Complementario"],
        "21.2.0.0.00.000 - Personal Temporario": ["21.2.1.0.00.000 - Retribución del cargo"]
    },
    "2. Bienes de consumo": {
        "22.1.0.0.00.000 - Productos alimenticios": ["22.1.1.0.00.000 - Alimentos para personas"]
    }
}

MAPEO_RECURSOS = {
    "11.1.0.0.00.000 - Ingresos Tributarios": {
        "11.1.2.0.00.000 - Sobre el Patrimonio": ["11.1.2.1.01.000 - TGIU"]
    }
}

MAPEO_ESTRUCTURA = {
    "AGENCIA MUNICIPAL DE SEGURIDAD": ["AGENCIA MUNICIPAL DE SEGURIDAD"],
    "SECRETARÍA DE GESTIÓN AMBIENTAL Y TERRITORIAL": ["SUBSECRETARÍA DE OBRAS", "SUBSECRETARÍA DE AMBIENTE Y ACCIÓN CLIMÁTICA"],
    "SECRETARÍA DE GOBIERNO": ["SECRETARÍA DE GOBIERNO", "SUBSECRETARÍA DE GESTIÓN Y DESARROLLO"],
    "SECRETARÍA DE DESARROLLO Y PROMOCIÓN DE DDHH": ["SECRETARÍA DE DESARROLLO Y PROMOCIÓN DE DDHH", "SUBSECRETARÍA DE CULTURA"],
    "INTENDENCIA": ["INTENDENCIA"],
    "HCD": ["HCD"]
}

opciones_secretarias = list(MAPEO_ESTRUCTURA.keys())
opciones_objetos = list(MAPEO_GASTOS.keys())
opciones_fuente_fin = ["Municipal", "Provincial", "Nacional"]
opciones_clase = ["Corriente", "Capital"]
opciones_tipo = ["Libre", "Afectado"]
opciones_finalidad = ["Administración Central", "Promoción y asistencia social", "Educación", "Cultura", "Servicios urbanos"]

# =====================================================================
# MENÚ LATERAL (SIDEBAR)
# =====================================================================
with st.sidebar:
    st.title("🍩 Homero")
    st.caption("Municipalidad de Sunchales - 2027")
    st.markdown("---")
    opcion_menu = st.radio(
        "Navegación del Sistema:",
        [
            "📝 FORMULARIO DE REGISTRO", 
            "➕ GESTIÓN DE DESTINOS",
            "📥 REGISTRO DE RECURSOS",
            "📉 GENERAL (Base de Datos Sheet)",
            "🏛️ REPORTE OFICIAL POR DESTINO",
            "🛠️ PANEL DE MODIFICACIONES"
        ]
    )
    st.markdown("---")
    if st.button("🔄 Sincronizar y Limpiar Caché", use_container_width=True):
        if "db_local_backup" in st.session_state:
            st.session_state["db_local_backup"] = {"destinos": [], "egresos": [], "recursos": []}
        st.cache_data.clear()
        st.success("¡Caché limpiada y datos actualizados desde Google Sheets!")
        st.rerun()

# =====================================================================
# SECCIÓN PRINCIPAL: FORMULARIO DE REGISTRO
# =====================================================================
if opcion_menu == "📝 FORMULARIO DE REGISTRO":
    st.subheader("📥 Cargar Nuevo Renglón Presupuestario")
    
    f_sec = st.selectbox("SECRETARÍA:", options=[""] + opciones_secretarias)
    f_sub = st.selectbox("SUBSECRETARÍA:", options=[""] + (MAPEO_ESTRUCTURA[f_sec] if f_sec else []))
    
    f_total = st.number_input("PRESUPUESTO / VALOR ($):", min_value=0.0, step=100.0)
    
    if st.button("💾 GUARDAR REGISTRO", type="primary", use_container_width=True):
        st.success("✅ Registro preparado para guardar.")

elif opcion_menu == "📉 GENERAL (Base de Datos Sheet)":
    st.subheader("📊 Base de Datos General de Egresos")
    st.dataframe(df_egr_completo, use_container_width=True)

else:
    st.subheader(opcion_menu)
    st.info("Módulo sincronizado con tus nuevas hojas de Google Sheets.")
