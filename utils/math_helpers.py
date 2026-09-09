import streamlit as st

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

def aplicar_estilos_base():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
            html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
            .stApp { background-color: #ffffff; }
            [data-testid="stSidebar"] { background-color: #0a0a0a; color: #ffffff; }
            [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: #ffffff !important; }
        </style>
    """, unsafe_allow_html=True)
