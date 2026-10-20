import streamlit as st
import pandas as pd
import requests
import io

# Configuración de la página
st.set_page_config(page_title="Evaluación Ejecución Presupuestaria", layout="wide")

# Parámetros oficiales de tu documento
SPREADSHEET_ID = "1rDFoL0KPCiqmo1pBobrRuibAwtT9anRPZPLgjrPCBWo"
GID_EVALUACION = "162541600" 

url_evaluacion = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GID_EVALUACION}"

@st.cache_data(ttl=60)
def cargar_evaluacion():
    try:
        resp = requests.get(url_evaluacion, timeout=30)
        if resp.status_code == 200:
            df = pd.read_csv(io.StringIO(resp.text))
            df = df.fillna("")
            return df
        else:
            return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# Encabezado institucional idéntico al documento oficial
st.markdown("""
<div style="border: 2px solid #333; padding: 20px; border-radius: 6px; background-color: #f9f9f9; font-family: Arial, sans-serif;">
    <table style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="width: 35%; font-size: 13px; text-align: left;">
                <b>MUNICIPALIDAD DE SUNCHALES</b><br>
                <span style="font-size: 11px; color: #555;">Sistema Presupuestario Municipal</span>
            </td>
            <td style="width: 45%; text-align: center;">
                <h3 style="margin: 0; font-size: 17px; color: #222;">EVALUACIÓN EJECUCIÓN PRESUPUESTARIA</h3>
                <span style="font-size: 12px; color: #666;">Gasto por Objeto - 2026 (-140 Años-)</span>
            </td>
            <td style="width: 20%; text-align: right; font-size: 11px;">
                <b>Documento Oficial</b>
            </td>
        </tr>
    </table>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Cargar y mostrar los datos tal cual figuran en la hoja
df_datos = cargar_evaluacion()

if not df_datos.empty:
    st.success("✅ Datos cargados correctamente desde tu Google Sheet oficial.")
    
    # Visualización tabular interactiva idéntica a la planilla
    st.dataframe(df_datos, use_container_width=True, hide_index=True)
else:
    st.warning("⚠️ No se pudieron recuperar los datos. Comprobá que la hoja esté pública y publicada en la web como archivo CSV.")
