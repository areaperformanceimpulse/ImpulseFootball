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

@st.cache_data(ttl=300, show_spinner=False)
def fetch_datos_academia():
    res_jugadores = supabase.table("jugadores").select("*").execute()
    res_val = supabase.table("valoraciones_condicionales").select("*").execute()
    return res_jugadores.data, res_val.data

def cargar_datos_sistema():
    try:
        jugadores, valoraciones = fetch_datos_academia()
        st.session_state.jugadores = jugadores if jugadores else []
        st.session_state.valoraciones = valoraciones if valoraciones else []
        st.session_state.datos_cargados = True
        return True
    except Exception as e:
        st.error(f"Error al conectar con Supabase: {e}")
        return False

def guardar_datos_supabase(tabla, datos):
    try:
        supabase.table(tabla).insert(datos).execute()
        fetch_data_cache_clear = fetch_datos_academia.clear()
        cargar_datos_sistema()
        return True
    except Exception as e:
        st.error(f"Error al guardar en la base de datos: {e}")
        return False
