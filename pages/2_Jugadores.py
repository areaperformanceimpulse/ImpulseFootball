import streamlit as st
from database.db_manager import supabase, cargar_datos_sistema
from utils.math_helpers import aplicar_estilos_base
from datetime import date

st.set_page_config(page_title="Jugadores - ImpulseFootball", page_icon="👥", layout="wide")
aplicar_estilos_base()

if not st.session_state.get("autenticado", False):
    st.warning("Sesión caducada.")
    st.stop()

st.title("👥 Directorio de Deportistas")

tab_academy, tab_elite, tab_promise, tab_mod = st.tabs(["🟢 Academy", "🔵 Elite", "🟣 Promise", "⚙️ Modificar Jugadores"])

jugadores = st.session_state.get("jugadores", [])

def mostrar_lista_programa(prog_nombre):
    filtrados = [j for j in jugadores if j.get("programa") == prog_nombre]
    if not filtrados:
        st.info(f"No hay deportistas en el programa {prog_nombre}.")
    else:
        for j in filtrados:
            with st.container():
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.markdown(f"### 👤 {j.get('nombre')}")
                c2.markdown(f"**Posición:** {j.get('posicion', '-')}")
                if c3.button("Ver Historial", key=f"per_{j.get('id')}"):
                    st.session_state.jugador_activo_id = j.get('id')
                    st.switch_page("pages/4_Valoraciones.py")
                st.markdown("---")

with tab_academy:
    st.markdown("### Deportistas - Nivel Academy")
    mostrar_lista_programa("Academy")

with tab_elite:
    st.markdown("### Deportistas - Nivel Elite")
    mostrar_lista_programa("Elite")

with tab_promise:
    st.markdown("### Deportistas - Nivel Promise")
    mostrar_lista_programa("Promise")

with tab_mod:
    st.markdown("### ➕ Registrar Nuevo Deportista")
    with st.form("form_alta"):
        c1, c2 = st.columns(2)
        nombre_n = c1.text_input("Nombre y Apellidos:")
        prog_n = c2.selectbox("Programa:", ["Academy", "Elite", "Promise"])
        pos_n = st.selectbox("Posición:", ["Portero", "Lateral", "Central", "Mediocentro", "Extremo", "Delantero"])
        fn_n = st.date_input("Fecha Nacimiento:", value=date(2005, 1, 1))
        
        if st.form_submit_button("Guardar en Base de Datos"):
            if nombre_n.strip():
                supabase.table("jugadores").insert({
                    "nombre": nombre_n.strip(), "programa": prog_n, "posicion": pos_n, "fecha_nacimiento": str(fn_n)
                }).execute()
                cargar_datos_sistema()
                st.success(f"Deportista {nombre_n} registrado.")
                st.rerun()

    st.markdown("---")
    st.markdown("### ❌ Eliminar Deportista")
    if jugadores:
        nombres_dict = {j['nombre']: j['id'] for j in jugadores}
        a_borrar = st.selectbox("Selecciona deportista a eliminar:", list(nombres_dict.keys()))
        if st.button("Confirmar Eliminación"):
            supabase.table("jugadores").delete().eq("id", nombres_dict[a_borrar]).execute()
            cargar_datos_sistema()
            st.warning(f"Deportista {a_borrar} eliminado.")
            st.rerun()
