import streamlit as st
from supabase import create_client

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# Mantenemos la sesión activa
if "access_token" in st.session_state and "refresh_token" in st.session_state:
    try:
        supabase.auth.set_session(st.session_state.access_token, st.session_state.refresh_token)
    except:
        pass

@st.cache_data(ttl=600, show_spinner=False)
def fetch_datos_globales():
    """Descarga los jugadores y valoraciones de la academia"""
    res_jugadores = supabase.table("jugadores").select("*").execute()
    res_valoraciones = supabase.table("valoraciones_condicionales").select("*").execute()
    return res_jugadores.data, res_valoraciones.data

def cargar_datos_academia():
    """Carga los datos en memoria (session_state)"""
    try:
        jugadores, valoraciones = fetch_datos_globales()
        
        st.session_state.jugadores = jugadores
        st.session_state.valoraciones = valoraciones
        st.session_state.datos_cargados = True
        return True
    except Exception as e:
        st.error(f"Error al cargar desde Supabase: {e}")
        return False
