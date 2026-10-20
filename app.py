import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Configuración inicial de la página
st.set_page_config(page_title="Sistema Presupuestario Unificado", layout="wide")

st.title("📊 Sistema de Registro Presupuestario")
st.markdown("Aplicación conectada a múltiples hojas de cálculo de Google Sheets.")

# --- CONEXIÓN A GOOGLE SHEETS (Lectura y Escritura) ---
@st.cache_resource
def conectar_google_sheets():
    # Obtenemos las credenciales desde los secrets seguros de Streamlit
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client

try:
    cliente = conectar_google_sheets()
    
    # 1. CARGAR LAS 3 HOJAS DE CÁLCULO
    # Puedes usar el ID de cada hoja (lo que está entre /d/ y /edit en tus URLs)
    
    # ID Hoja 1 (Ejemplo: Presupuesto)
    hoja_1 = cliente.open_by_key("1JLCDkHYiSFV_cCOjVigcIXLkpD61pHpoxOmJ1CvK2m4")
    datos_h1 = pd.DataFrame(hoja_1.sheet1.get_all_records())

    # ID Hoja 2 (Ejemplo: Gastos o Recursos)
    hoja_2 = cliente.open_by_key("1KvqGJlJEu4KdRXXuxHET-2b1KP8vm4q-tb7_JR10iu8")
    datos_h2 = pd.DataFrame(hoja_2.sheet1.get_all_records())

    # ID Hoja 3 (La hoja que usarás para ingresar modificaciones/datos nuevos)
    hoja_3 = cliente.open_by_key("1mFfZ2dA6QVoYroYPTcF67eIsuba3uBXnR1_bBAvgGs8")
    worksheet_modificaciones = hoja_3.sheet1
    datos_h3 = pd.DataFrame(worksheet_modificaciones.get_all_records())

    # --- PESTAÑAS DE LA INTERFAZ ---
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Resumen General", "📂 Hoja 1", "📂 Hoja 2", "✍️ Registrar / Modificar Datos"])

    with tab1:
        st.subheader("Vista unificada de tus datos")
        col1, col2, col3 = st.columns(3)
        col1.metric("Registros en H1", len(datos_h1))
        col2.metric("Registros en H2", len(datos_h2))
        col3.metric("Registros en H3", len(datos_h3))

    with tab2:
        st.subheader("Contenido de la Hoja 1")
        st.dataframe(datos_h1, use_container_width=True)

    with tab3:
        st.subheader("Contenido de la Hoja 2")
        st.dataframe(datos_h2, use_container_width=True)

    with tab4:
        st.subheader("Ingresar nuevos datos (Hoja 3 modificable)")
        st.dataframe(datos_h3, use_container_width=True)
        
        st.markdown("---")
        st.write("### Agregar un nuevo registro:")
        
        # Formulario dinámico para registrar información en tiempo real
        with st.form("form_nuevo_registro"):
            # Ajusta estos campos según las columnas reales que tenga tu Hoja 3
            campo_1 = st.text_input("Concepto / Descripción")
            campo_2 = st.number_input("Monto / Valor", min_value=0.0, step=0.01)
            campo_3 = st.selectbox("Categoría / Estado", ["Activo", "Pendiente", "Cerrado"])
            
            submit = st.form_submit_button("Guardar en Google Sheets")
            
            if submit:
                # Añade la nueva fila directamente al Google Sheet de la Hoja 3
                worksheet_modificaciones.append_row([campo_1, campo_2, campo_3])
                st.success("¡Datos guardados y sincronizados correctamente en Google Sheets!")
                st.rerun()

except Exception as e:
    st.error(f"Error al conectar con las hojas de cálculo. Verifica tus credenciales o los IDs de las hojas. Detalle: {e}")
