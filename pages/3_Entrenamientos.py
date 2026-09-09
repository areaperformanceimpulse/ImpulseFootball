import streamlit as st
from utils.math_helpers import aplicar_estilos_base

st.set_page_config(page_title="Entrenamientos - ImpulseFootball", page_icon="📋", layout="wide")
aplicar_estilos_base()

if not st.session_state.get("autenticado", False):
    st.warning("Sesión caducada.")
    st.stop()

st.title("📋 Control de Entrenamientos")
st.markdown("Registro de cargas, asistencia y planificación de sesiones técnicas, tácticas y condicionales.")

st.info("Módulo de entrenamientos preparado para registrar las sesiones del día.")
