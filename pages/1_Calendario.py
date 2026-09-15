import streamlit as st
from database.db_manager import supabase, cargar_datos_sistema
from utils.math_helpers import aplicar_estilos_base
from datetime import date
import pandas as pd

st.set_page_config(page_title="Calendario - ImpulseFootball", page_icon="📅", layout="wide")
aplicar_estilos_base()

if not st.session_state.get("autenticado", False):
    st.warning("Sesión caducada.")
    st.stop()

# Asegurar que los datos están actualizados
cargar_datos_sistema()

st.title("📅 Calendario de Entrenamientos")

tab_nueva, tab_historial = st.tabs(["➕ Programar Nueva Sesión", "🗓️ Historial de Sesiones"])

jugadores = st.session_state.get("jugadores", [])
sesiones = st.session_state.get("sesiones", [])

# ==========================================
# PESTAÑA 1: NUEVA SESIÓN
# ==========================================
with tab_nueva:
    st.markdown("### 📝 Configurar Sesión Diaria")
    
    if not jugadores:
        st.warning("No hay deportistas registrados en el sistema.")
    else:
        # Layout del formulario
        c1, c2 = st.columns([1, 1])
        
        with c1:
            fecha_sesion = st.date_input("Fecha del Entrenamiento:", value=date.today())
            programa_sel = st.selectbox("Programa de Entrenamiento:", options=["Academy", "Elite", "Promise"])
            
            # Filtro dinámico: Solo mostramos los jugadores del programa seleccionado
            jugadores_filtrados = [j for j in jugadores if j.get("programa") == programa_sel]
            nombres_filtrados = [j["nombre"] for j in jugadores_filtrados]
            
            asistentes = st.multiselect(
                f"Deportistas Convocados ({len(nombres_filtrados)} disponibles):", 
                options=nombres_filtrados,
                default=nombres_filtrados # Por defecto, selecciona a todos los del grupo
            )
            
        with c2:
            comentarios = st.text_area("Foco de la Sesión (Técnico / Táctico / Condicional):", height=200, placeholder="Ej: Sesión enfocada en transiciones ofensivas y trabajo de fuerza explosiva en campo...")
            
        st.markdown("---")
        
        if st.button("💾 Guardar Sesión", use_container_width=True):
            if not asistentes:
                st.error("Debes seleccionar al menos un deportista para la sesión.")
            else:
                try:
                    nueva_sesion = {
                        "fecha": str(fecha_sesion),
                        "programa": programa_sel,
                        "asistentes": asistentes, # Supabase lo convertirá automáticamente a JSONB
                        "comentarios": comentarios
                    }
                    supabase.table("sesiones_entrenamiento").insert(nueva_sesion).execute()
                    cargar_datos_sistema()
                    st.success(f"¡Sesión del {fecha_sesion} guardada correctamente para el grupo {programa_sel}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar la sesión: {e}")

# ==========================================
# PESTAÑA 2: HISTORIAL
# ==========================================
with tab_historial:
    st.markdown("### 🗓️ Registro Histórico")
    
    if not sesiones:
        st.info("Aún no hay sesiones registradas en el calendario.")
    else:
        # Convertimos a DataFrame para facilitar la gestión
        df_sesiones = pd.DataFrame(sesiones)
        df_sesiones = df_sesiones.sort_values(by="fecha", ascending=False)
        
        # Filtros de visualización
        cf1, cf2 = st.columns(2)
        with cf1:
            filtro_prog = st.selectbox("Filtrar por Programa:", ["Todos", "Academy", "Elite", "Promise"])
        
        if filtro_prog != "Todos":
            df_sesiones = df_sesiones[df_sesiones["programa"] == filtro_prog]
            
        st.markdown("---")
        
        # Mostrar las sesiones de forma visual y estructurada
        if df_sesiones.empty:
            st.warning("No hay sesiones que coincidan con el filtro.")
        else:
            for idx, row in df_sesiones.iterrows():
                with st.expander(f"📌 {row['fecha']} - Grupo {row['programa']} ({len(row['asistentes'])} asistentes)"):
                    c_det1, c_det2 = st.columns([2, 1])
                    with c_det1:
                        st.markdown("**📝 Foco de la Sesión:**")
                        st.write(row["comentarios"] if row["comentarios"] else "Sin observaciones registradas.")
                    with c_det2:
                        st.markdown("**👥 Asistentes:**")
                        for jugador in row["asistentes"]:
                            st.write(f"- {jugador}")
