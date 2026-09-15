import streamlit as st
import os

def aplicar_estilos_base():
    """
    Lee el archivo style.css puro y lo inyecta en la aplicación de Streamlit.
    """
    # Construimos la ruta absoluta al archivo style.css (que está en la misma carpeta)
    css_path = os.path.join(os.path.dirname(__file__), "style.css")
    
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("No se encontró el archivo style.css en la carpeta Utils.")

def safe_float(val):
    try:
        if val is None or val == "" or str(val).lower() == "nan": return 0.0
        return float(val)
    except:
        return 0.0

def calcular_asimetria(der, izq):
    d, i = safe_float(der), safe_float(izq)
    if max(d, i) == 0: return 0.0
    return round((abs(d - i) / max(d, i)) * 100, 1)
