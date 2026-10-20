import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Sistema Presupuestario Unificado", layout="wide")

st.title("📊 Sistema de Registro Presupuestario")
st.markdown("Aplicación conectada a Google Sheets de forma gratuita.")

# --- CARGAR LAS HOJAS MEDIANTE ENLACES CSV PÚBLICOS ---
# (Para obtener estas URLs: En tu Google Sheet ve a Archivo > Compartir > Publicar en la web > Selecciona CSV y copia el enlace)

@st.cache_data(ttl=60) # Recarga los datos cada minuto para ver cambios recientes
def cargar_hojas():
    try:
        # Reemplaza estas URLs con los enlaces CSV públicos de tus 3 hojas de Google
        url_h1 = "URL_CSV_DE_LA_HOJA_1"
        url_h2 = "URL_CSV_DE_LA_HOJA_2"
        url_h3 = "URL_CSV_DE_LA_HOJA_3"
        
        df1 = pd.read_csv(url_h1)
        df2 = pd.read_csv(url_h2)
        df3 = pd.read_csv(url_h3)
        return df1, df2, df3
    except Exception as e:
        return None, None, None

df1, df2, df3 = cargar_hojas()

if df1 is not None:
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Resumen", "📂 Hoja 1", "📂 Hoja 2", "✍️ Hoja de Modificaciones"])

    with tab1:
        st.subheader("Estado general")
        st.metric("Total de registros en Hoja 3", len(df3) if df3 is not None else 0)

    with tab2:
        st.subheader("Datos de la Hoja 1")
        st.dataframe(df1, use_container_width=True)

    with tab3:
        st.subheader("Datos de la Hoja 2")
        st.dataframe(df2, use_container_width=True)

    with tab4:
        st.subheader("Registros actuales (Hoja 3)")
        st.dataframe(df3, use_container_width=True)
        
        st.info("💡 Para ingresar datos nuevos de forma interactiva y gratuita, puedes usar un Formulario de Google vinculado a esta hoja, o configurar un Web App de Google Apps Script.")
else:
    st.warning("⚠️ Por favor, publica tus 3 hojas de Google Sheets como CSV y pega las URLs en el código para visualizarlas.")
