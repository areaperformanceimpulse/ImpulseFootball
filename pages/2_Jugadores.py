import streamlit as st
from database.db_manager import supabase, cargar_datos_sistema
from utils.math_helpers import aplicar_estilos_base
import pandas as pd

st.set_page_config(page_title="Jugadores - ImpulseFootball", page_icon="⚽", layout="wide")
aplicar_estilos_base()

if not st.session_state.get("autenticado", False):
    st.warning("Sesión caducada.")
    st.stop()

cargar_datos_sistema()

st.title("⚽ Gestión de Deportistas")

tab_lista, tab_nuevo = st.tabs(["👥 Listado por Programas", "➕ Registrar Nuevo Deportista"])

jugadores = st.session_state.get("jugadores", [])

# ==========================================
# PESTAÑA 1: LISTADO POR PROGRAMAS Y PERFIL
# ==========================================
with tab_lista:
    st.markdown("### 📋 Plantilla de Deportistas por Programa")
    
    if not jugadores:
        st.info("No hay deportistas registrados todavía.")
    else:
        # Programas solicitados
        programas = ["Academy", "Elite", "Promise"]
        
        # Creamos pestañas dinámicas por programa
        tabs_prog = st.tabs(programas)
        
        for idx, prog in enumerate(programas):
            with tabs_prog[idx]:
                # Filtramos jugadores de este programa
                jugadores_prog = [j for j in jugadores if j.get("programa") == prog]
                
                if not jugadores_prog:
                    st.markdown(f"*No hay jugadores registrados en el programa {prog}.*")
                else:
                    st.markdown(f"#### Programa: {prog} ({len(jugadores_prog)} jugadores)")
                    
                    for jugador in jugadores_prog:
                        with st.container(border=True):
                            col_info1, col_info2, col_info3, col_btn = st.columns([2, 2, 2, 1])
                            
                            with col_info1:
                                st.markdown(f"**👤 {jugador.get('nombre')}**")
                                st.caption(f"Categoría: {jugador.get('categoria_edad', 'N/D')}")
                                
                            with col_info2:
                                st.markdown(f"🏟️ **Club:** {jugador.get('club', 'No especificado')} ({jugador.get('categoria_club', 'N/D')})")
                                
                            with col_info3:
                                st.markdown(f"📐 **Altura:** {jugador.get('altura', '---')} cm | 🦵 **Pierna:** {jugador.get('pierna_dominante', 'N/D')}")
                                
                            with col_btn:
                                st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
                                if st.button("📁 Perfil", key=f"btn_perfil_{jugador.get('id')}", use_container_width=True):
                                    st.info(f"Próximamente: Vista de perfil detallado e histórico de {jugador.get('nombre')}.")

# ==========================================
# PESTAÑA 2: REGISTRAR NUEVO DEPORTISTA
# ==========================================
with tab_nuevo:
    st.markdown("### 📝 Formulario de Alta de Deportista")
    
    with st.form("form_nuevo_jugador"):
        c1, c2, c3 = st.columns(3)
        
        with c1:
            nombre = st.text_input("Nombre y Apellidos del Deportista:")
            programa = st.selectbox("Programa Interno:", options=["Academy", "Elite", "Promise"])
            categoria_edad = st.selectbox(
                "Categoría de Edad:", 
                options=["Benjamín", "Alevín", "Infantil", "Cadete", "Juvenil", "Sénior"]
            )
            
        with c2:
            club = st.text_input("Club Actual / Procedencia:", placeholder="Ej: RC Celta, Coruxo FC...")
            categoria_club = st.text_input("Categoría del Club:", placeholder="Ej: División de Honor, Liga Autonómica...")
            
        with c3:
            pierna_dominante = st.selectbox("Pierna Dominante:", options=["Derecha", "Izquierda", "Ambidextra"])
            altura = st.number_input("Altura (cm):", min_value=100.0, max_value=220.0, value=170.0, step=0.5)
            
        st.markdown("---")
        
        if st.form_submit_button("💾 Guardar Deportista", use_container_width=True):
            if not nombre.strip():
                st.error("El nombre del deportista es obligatorio.")
            else:
                try:
                    nuevo_jugador = {
                        "nombre": nombre.strip(),
                        "programa": programa,
                        "categoria_edad": categoria_edad,
                        "club": club.strip() if club else None,
                        "categoria_club": categoria_club.strip() if categoria_club else None,
                        "pierna_dominante": pierna_dominante,
                        "altura": float(altura)
                    }
                    
                    supabase.table("jugadores").insert(nuevo_jugador).execute()
                    cargar_datos_sistema()
                    st.success(f"¡Deportista '{nombre}' registrado correctamente!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al registrar al jugador: {e}")
