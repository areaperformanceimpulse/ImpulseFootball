import streamlit as st
from supabase import create_client

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

if "access_token" in st.session_state and "refresh_token" in st.session_state:
    try:
        supabase.auth.set_session(st.session_state.access_token, st.session_state.refresh_token)
    except:
        pass

# 1. Definimos la caché con un TTL (Time To Live) de 5 minutos (300s)
@st.cache_data(ttl=300, show_spinner=False)
def fetch_datos_academia():
    """Descarga los datos de Supabase y los almacena en caché."""
    res_jugadores = supabase.table("jugadores").select("*").execute()
    res_val = supabase.table("valoraciones_condicionales").select("*").execute()
    res_sesiones = supabase.table("sesiones_entrenamiento").select("*").execute()
    
    return (
        res_jugadores.data if res_jugadores.data else [],
        res_val.data if res_val.data else [],
        res_sesiones.data if res_sesiones.data else []
    )

def cargar_datos_sistema(force_refresh=False):
    """
    Carga los datos en st.session_state utilizando la caché.
    Si force_refresh=True, limpia la caché primero para forzar la recarga desde la base de datos.
    """
    if force_refresh:
        fetch_datos_academia.clear()
        
    try:
        # Llamamos a la función cacheada (si no hay force_refresh, esto es instantáneo)
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

def guardar_datos_supabase(tabla, datos):
    try:
        supabase.table(tabla).insert(datos).execute()
        # Forzamos la actualización de la caché al guardar un dato nuevo
        cargar_datos_sistema(force_refresh=True)
        return True
    except Exception as e:
        st.error(f"Error al guardar en la base de datos: {e}")
        return False
