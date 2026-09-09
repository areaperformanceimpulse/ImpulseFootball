import streamlit as st
from database.db_manager import supabase, cargar_datos_sistema
from utils.math_helpers import aplicar_estilos_base

st.set_page_config(page_title="ImpulseFootball - Condicional", page_icon="⚡", layout="wide")
aplicar_estilos_base()

if "autenticado" not in st.session_state: st.session_state.autenticado = False
if "jugadores" not in st.session_state: st.session_state.jugadores = []
if "valoraciones" not in st.session_state: st.session_state.valoraciones = []

if not st.session_state.autenticado:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<h1 style='text-align: center; font-weight: 800;'>IMPULSE<span style='color: #dc2626;'>FOOTBALL</span></h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b; margin-bottom: 30px;'>Gestión de Rendimiento Condicional</p>", unsafe_allow_html=True)
        
        tab_log, tab_reg = st.tabs(["INICIAR SESIÓN", "REGISTRAR STAFF"])
        
        with tab_log:
            with st.form("login_staff"):
                email = st.text_input("Correo electrónico")
                password = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Acceder al Sistema", use_container_width=True):
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.usuario_id = res.user.id
                        st.session_state.access_token = res.session.access_token
                        st.session_state.refresh_token = res.session.refresh_token
                        st.session_state.autenticado = True
                        cargar_datos_sistema()
                        st.success("¡Bienvenido!")
                        st.rerun()
                    except Exception as e:
                        st.error("Credenciales incorrectas o error de conexión.")
                        
        with tab_reg:
            with st.form("reg_staff"):
                r_email = st.text_input("Correo electrónico")
                r_pass = st.text_input("Contraseña (mín. 6 caracteres)", type="password")
                if st.form_submit_button("Crear Cuenta de Entrenador", use_container_width=True):
                    try:
                        supabase.auth.sign_up({"email": r_email, "password": r_pass})
                        st.success("¡Cuenta creada con éxito! Ya puedes iniciar sesión.")
                    except Exception as e:
                        st.error(f"Error al registrar: {e}")
    st.stop()

# Si ya está autenticado, cargamos la pantalla principal
if not st.session_state.get("datos_cargados", False):
    cargar_datos_sistema()

st.title("⚡ Panel de Control Condicional")
st.markdown("---")

total_jugadores = len(st.session_state.jugadores)
total_vals = len(st.session_state.valoraciones)

col1, col2, col3 = st.columns(3)
col1.metric("Deportistas Registrados", total_jugadores)
col2.metric("Valoraciones Totales", total_vals)
col3.metric("Programas Activos", "Academy, Elite, Promise")

st.markdown("### 🚀 Accesos Directos")
c_a, c_b, c_c = st.columns(3)
with c_a:
    if st.button("👥 Directorio de Jugadores", use_container_width=True):
        st.switch_page("pages/1_Directorio_Jugadores.py")
with c_b:
    if st.button("📝 Nueva Valoración (Gimnasio)", use_container_width=True):
        st.switch_page("pages/2_Nueva_Valoracion.py")
with c_c:
    if st.button("📈 Perfil y Progreso", use_container_width=True):
        st.switch_page("pages/3_Perfil_y_Progreso.py")
