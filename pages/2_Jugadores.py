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

# Añadimos la tercera pestaña para modificar
tab_lista, tab_nuevo, tab_editar = st.tabs(["👥 Listado por Programas", "➕ Registrar Nuevo Deportista", "✏️ Modificar Deportista"])

jugadores = st.session_state.get("jugadores", [])

# ==========================================
# PESTAÑA 1: LISTADO POR PROGRAMAS Y PERFIL
# ==========================================
with tab_lista:
    st.markdown("### 📋 Plantilla de Deportistas por Programa")
    
    if not jugadores:
        st.info("No hay deportistas registrados todavía.")
    else:
        programas = ["Academy", "Elite", "Promise"]
        tabs_prog = st.tabs(programas)
        
        for idx, prog in enumerate(programas):
            with tabs_prog[idx]:
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
                    cargar_datos_sistema(force_refresh=True)
                    st.success(f"¡Deportista '{nombre}' registrado correctamente!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al registrar al jugador: {e}")

# ==========================================
# PESTAÑA 3: MODIFICAR DEPORTISTA
# ==========================================
with tab_editar:
    st.markdown("### ✏️ Modificar Datos de Deportista")
    
    if not jugadores:
        st.info("No hay deportistas para modificar.")
    else:
        # Diccionario para seleccionar jugador por ID y mostrar su nombre y programa
        opciones_jugadores = {j['id']: f"{j.get('nombre')} ({j.get('programa')} - {j.get('categoria_edad', 'Sin cat')})" for j in jugadores}
        
        jugador_editar_id = st.selectbox(
            "Selecciona al deportista a modificar:", 
            options=list(opciones_jugadores.keys()), 
            format_func=lambda x: opciones_jugadores[x]
        )
        
        jugador_actual = next((j for j in jugadores if j['id'] == jugador_editar_id), None)
        
        if jugador_actual:
            with st.form("form_editar_jugador"):
                # Índices predeterminados para los selects según los datos actuales
                list_prog = ["Academy", "Elite", "Promise"]
                idx_prog = list_prog.index(jugador_actual.get('programa')) if jugador_actual.get('programa') in list_prog else 0
                
                list_cat = ["Benjamín", "Alevín", "Infantil", "Cadete", "Juvenil", "Sénior"]
                cat_actual = jugador_actual.get('categoria_edad')
                idx_cat = list_cat.index(cat_actual) if cat_actual in list_cat else 0
                
                list_pierna = ["Derecha", "Izquierda", "Ambidextra"]
                pierna_actual = jugador_actual.get('pierna_dominante')
                idx_pierna = list_pierna.index(pierna_actual) if pierna_actual in list_pierna else 0

                ec1, ec2, ec3 = st.columns(3)
                
                with ec1:
                    e_nombre = st.text_input("Nombre y Apellidos:", value=jugador_actual.get('nombre', ''))
                    e_programa = st.selectbox("Programa Interno:", options=list_prog, index=idx_prog)
                    e_categoria_edad = st.selectbox("Categoría de Edad:", options=list_cat, index=idx_cat)
                    
                with ec2:
                    e_club = st.text_input("Club Actual / Procedencia:", value=jugador_actual.get('club', '') or '')
                    e_categoria_club = st.text_input("Categoría del Club:", value=jugador_actual.get('categoria_club', '') or '')
                    
                with ec3:
                    e_pierna = st.selectbox("Pierna Dominante:", options=list_pierna, index=idx_pierna)
                    e_altura = st.number_input("Altura (cm):", min_value=100.0, max_value=220.0, value=float(jugador_actual.get('altura', 170.0) or 170.0), step=0.5)
                    
                st.markdown("---")
                
                if st.form_submit_button("🔄 Actualizar Datos del Deportista", use_container_width=True):
                    if not e_nombre.strip():
                        st.error("El nombre del deportista no puede estar vacío.")
                    else:
                        try:
                            datos_actualizados = {
                                "nombre": e_nombre.strip(),
                                "programa": e_programa,
                                "categoria_edad": e_categoria_edad,
                                "club": e_club.strip() if e_club else None,
                                "categoria_club": e_categoria_club.strip() if e_categoria_club else None,
                                "pierna_dominante": e_pierna,
                                "altura": float(e_altura)
                            }
                            
                            supabase.table("jugadores").update(datos_actualizados).eq("id", jugador_editar_id).execute()
                            cargar_datos_sistema(force_refresh=True)
                            st.success(f"¡Datos de '{e_nombre}' actualizados correctamente!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al actualizar el deportista: {e}")
