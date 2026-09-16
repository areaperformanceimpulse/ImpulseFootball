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
                    
                    # Sistema de cuadrícula (grid) de 4 columnas para tarjetas más estrechas
                    cols_per_row = 4
                    for i in range(0, len(jugadores_prog), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for j, col in enumerate(cols):
                            if i + j < len(jugadores_prog):
                                jugador = jugadores_prog[i + j]
                                with col:
                                    with st.container(border=True):
                                        # Diseño de tarjeta vertical
                                        st.markdown("<div style='text-align: center; font-size: 4rem; margin-bottom: 10px;'>👤</div>", unsafe_allow_html=True)
                                        st.markdown(f"<div style='text-align: center;'><span style='font-size: 1.2rem; font-weight: 800; color: #09274e;'>{jugador.get('nombre')}</span><br><span style='font-size: 0.85rem; color: #64748b;'>{jugador.get('club', 'Sin club')} | {jugador.get('categoria_edad', 'N/D')}</span></div>", unsafe_allow_html=True)
                                        
                                        st.markdown("<div style='height: 15px'></div>", unsafe_allow_html=True)
                                        if st.button("📁 Perfil", key=f"btn_perfil_{jugador.get('id')}", use_container_width=True):
                                            st.info(f"Próximamente: Vista de perfil detallado e histórico de {jugador.get('nombre')}.")

# ==========================================
# PESTAÑA 2: REGISTRAR NUEVO DEPORTISTA
# ==========================================
with tab_nuevo:
    st.markdown("### 📝 Formulario de Alta de Deportista")
    
    with st.form("form_nuevo_jugador"):
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            nombre = st.text_input("Nombre y Apellidos:")
            programa = st.selectbox("Programa Interno:", options=["Academy", "Elite", "Promise"])
            
        with c2:
            club = st.text_input("Club Actual / Procedencia:", placeholder="Ej: RC Celta...")
            categoria_club = st.text_input("Categoría del Club:", placeholder="Ej: División de Honor...")
            
        with c3:
            categoria_edad = st.selectbox(
                "Categoría de Edad:", 
                options=["Benjamín", "Alevín", "Infantil", "Cadete", "Juvenil", "Sénior"]
            )
            altura = st.number_input("Altura (cm):", min_value=100.0, max_value=220.0, value=170.0, step=0.5)

        with c4:
            pierna_dominante = st.selectbox("Pierna Dominante:", options=["Derecha", "Izquierda", "Ambidextra"])
            brazo_dominante = st.selectbox("Brazo Dominante:", options=["Derecho", "Izquierdo", "Ambidextro"])
            
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
                        "brazo_dominante": brazo_dominante,
                        "altura": float(altura)
                    }
                    
                    supabase.table("jugadores").insert(nuevo_jugador).execute()
                    cargar_datos_sistema(force_refresh=True)
                    st.success(f"¡Deportista '{nombre}' registrado correctamente!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al registrar al jugador: {e}")

# ==========================================
# PESTAÑA 3: MODIFICAR / ELIMINAR DEPORTISTA
# ==========================================
with tab_editar:
    st.markdown("### ✏️ Modificar o Eliminar Deportista")
    
    if not jugadores:
        st.info("No hay deportistas para modificar.")
    else:
        opciones_jugadores = {j['id']: f"{j.get('nombre')} ({j.get('programa')} - {j.get('categoria_edad', 'Sin cat')})" for j in jugadores}
        
        jugador_editar_id = st.selectbox(
            "Selecciona al deportista a gestionar:", 
            options=list(opciones_jugadores.keys()), 
            format_func=lambda x: opciones_jugadores[x]
        )
        
        jugador_actual = next((j for j in jugadores if j['id'] == jugador_editar_id), None)
        
        if jugador_actual:
            with st.form("form_editar_jugador"):
                list_prog = ["Academy", "Elite", "Promise"]
                idx_prog = list_prog.index(jugador_actual.get('programa')) if jugador_actual.get('programa') in list_prog else 0
                
                list_cat = ["Benjamín", "Alevín", "Infantil", "Cadete", "Juvenil", "Sénior"]
                cat_actual = jugador_actual.get('categoria_edad')
                idx_cat = list_cat.index(cat_actual) if cat_actual in list_cat else 0
                
                list_pierna = ["Derecha", "Izquierda", "Ambidextra"]
                pierna_actual = jugador_actual.get('pierna_dominante')
                idx_pierna = list_pierna.index(pierna_actual) if pierna_actual in list_pierna else 0

                list_brazo = ["Derecho", "Izquierdo", "Ambidextro"]
                brazo_actual = jugador_actual.get('brazo_dominante')
                idx_brazo = list_brazo.index(brazo_actual) if brazo_actual in list_brazo else 0

                ec1, ec2, ec3, ec4 = st.columns(4)
                
                with ec1:
                    e_nombre = st.text_input("Nombre y Apellidos:", value=jugador_actual.get('nombre', ''))
                    e_programa = st.selectbox("Programa Interno:", options=list_prog, index=idx_prog)
                    
                with ec2:
                    e_club = st.text_input("Club Actual:", value=jugador_actual.get('club', '') or '')
                    e_categoria_club = st.text_input("Categoría del Club:", value=jugador_actual.get('categoria_club', '') or '')
                    
                with ec3:
                    e_categoria_edad = st.selectbox("Categoría de Edad:", options=list_cat, index=idx_cat)
                    e_altura = st.number_input("Altura (cm):", min_value=100.0, max_value=220.0, value=float(jugador_actual.get('altura', 170.0) or 170.0), step=0.5)

                with ec4:
                    e_pierna = st.selectbox("Pierna Dominante:", options=list_pierna, index=idx_pierna)
                    e_brazo = st.selectbox("Brazo Dominante:", options=list_brazo, index=idx_brazo)
                    
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
                                "brazo_dominante": e_brazo,
                                "altura": float(e_altura)
                            }
                            
                            supabase.table("jugadores").update(datos_actualizados).eq("id", jugador_editar_id).execute()
                            cargar_datos_sistema(force_refresh=True)
                            st.success(f"¡Datos de '{e_nombre}' actualizados correctamente!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al actualizar el deportista: {e}")

            # Botón de eliminación fuera del form para no interferir con la actualización
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Eliminar Deportista Definitivamente", type="primary", use_container_width=True):
                try:
                    supabase.table("jugadores").delete().eq("id", jugador_editar_id).execute()
                    cargar_datos_sistema(force_refresh=True)
                    st.success("¡Deportista eliminado correctamente!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al eliminar al deportista. Es posible que tenga valoraciones o sesiones asociadas que debas borrar primero: {e}")
