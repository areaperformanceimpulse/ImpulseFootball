import streamlit as st
from supabase import create_client

def get_supabase_client():
    """
    Crea y devuelve una instancia única de Supabase para cada usuario conectado,
    evitando que los tokens de sesión se sobreescriban entre diferentes dispositivos.
    """
    if "supabase_client" not in st.session_state:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        client = create_client(url, key)
        
        # Si el usuario ya se había logueado en esta sesión, restauramos sus tokens
        if "access_token" in st.session_state and "refresh_token" in st.session_state:
            try:
                client.auth.set_session(st.session_state.access_token, st.session_state.refresh_token)
            except:
                pass
                
        st.session_state.supabase_client = client
        
    return st.session_state.supabase_client

# 1. Definimos la caché con un TTL de 5 minutos (300s)
@st.cache_data(ttl=300, show_spinner=False)
def fetch_datos_academia():
    """Descarga los datos de Supabase y los almacena en caché."""
    # Para la caché global, usamos un cliente efímero que no interfiere con las sesiones de usuario
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    client_cache = create_client(url, key)
    
    res_jugadores = client_cache.table("jugadores").select("*").execute()
    res_val = client_cache.table("valoraciones_condicionales").select("*").execute()
    res_sesiones = client_cache.table("sesiones_entrenamiento").select("*").execute()
    
    return (
        res_jugadores.data if res_jugadores.data else [],
        res_val.data if res_val.data else [],
        res_sesiones.data if res_sesiones.data else []
    )

def cargar_datos_sistema(force_refresh=False):
    """Carga los datos en st.session_state utilizando la caché."""
    if force_refresh:
        fetch_datos_academia.clear()
        
    try:
        jugadores, valoraciones, sesiones = fetch_datos_academia()
        
        st.session_state.jugadores = jugadores
        st.session_state.valoraciones = valoraciones
        st.session_state.sesiones = sesiones
        
        st.session_state.datos_cargados = True
    except Exception as e:
        st.error(f"Error al cargar los datos del sistema: {e}")
        st.session_state.jugadores = []
        st.session_state.valoraciones = []
        st.session_state.sesiones = []
