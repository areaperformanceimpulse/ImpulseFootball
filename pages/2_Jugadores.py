import streamlit as st
from database.db_manager import get_supabase_client, cargar_datos_sistema
from utils.math_helpers import aplicar_estilos_base
import pandas as pd
from datetime import date

st.set_page_config(page_title="Jugadores - ImpulseFootball", page_icon="⚽", layout="wide")
aplicar_estilos_base()

supabase = get_supabase_client()

if not st.session_state.get("autenticado", False):
    st.warning("Sesión caducada.")
    st.stop()

cargar_datos_sistema()

st.title("⚽ Gestión de Deportistas y Temporadas")

# Utilidad para obtener la temporada por defecto
def get_temporada_actual():
    hoy = date.today()
    if hoy.month >= 9: return f"{str(hoy.year)[-2:]}/{str(hoy.year + 1)[-2:]}"
    else: return f"{str(hoy.year - 1)[-2:]}/{str(hoy.year)[-2:]}"

lista_temporadas = [f"{str(y)[-2:]}/{str(y+1)[-2:]}" for y in range(2024, 2031)]
lista_programas = ["Academy", "Elite", "Promise", "OffSeason"]
lista_categorias = ["Benjamín", "Alevín", "Infantil", "Cadete", "Juvenil", "Sénior"]

# Selector Global de Temporada para la Vista
st.markdown("### 🗓️ Contexto de Temporada")
temp_vista = st.selectbox("Selecciona la temporada que deseas gestionar o visualizar:", options=lista_temporadas, index=lista_temporadas.index(get_temporada_actual()) if get_temporada_actual() in lista_temporadas else 1)
st.markdown("---")

tab_lista, tab_nuevo, tab_editar = st.tabs(["👥 Listado por Programas", "➕ Registrar / Renovar Deportista", "✏️ Modificar / Eliminar"])

jugadores = st.session_state.get("jugadores", [])

# ==========================================
# PESTAÑA 1: LISTADO POR PROGRAMAS (Filtrado por temporada)
# ==========================================
with tab_lista:
    st.markdown(f"### 📋 Plantilla - Temporada {temp_vista}")
    
    if not jugadores:
        st.info("No hay deportistas registrados en la base de datos global.")
    else:
        # Extraemos solo los jugadores que tienen datos en la temporada seleccionada
        jugadores_temporada = []
        for j in jugadores:
            historial = j.get('historial_temporadas', {})
            if not isinstance(historial, dict): historial = {}
            
            # Si el jugador tiene un registro en esta temporada en su JSON
            if temp_vista in historial:
                datos_temp = historial[temp_vista]
                jugador_formateado = j.copy()
                jugador_formateado['programa_actual'] = datos_temp.get('programa', 'Sin Programa')
                jugador_formateado['club_actual'] = datos_temp.get('club', '')
                jugador_formateado['categoria_actual'] = datos_temp.get('categoria_edad', '')
                jugadores_temporada.append(jugador_formateado)

        if not jugadores_temporada:
            st.warning(f"No hay jugadores registrados específicamente en la temporada {temp_vista}.")
        else:
            tabs_prog = st.tabs(lista_programas)
            for idx, prog in enumerate(lista_programas):
                with tabs_prog[idx]:
                    jugadores_prog = [j for j in jugadores_temporada if j.get("programa_actual") == prog]
                    
                    if not jugadores_prog:
                        st.markdown(f"*No hay jugadores en el programa {prog} durante la {temp_vista}.*")
                    else:
                        st.markdown(f"#### Programa: {prog} ({len(jugadores_prog)} jugadores)")
                        
                        cols_per_row = 4
                        for i in range(0, len(jugadores_prog), cols_per_row):
                            cols = st.columns(cols_per_row)
                            for j_col, col in enumerate(cols):
                                if i + j_col < len(jugadores_prog):
                                    jugador = jugadores_prog[i + j_col]
                                    with col:
                                        with st.container(border=True):
                                            st.markdown("<div style='text-align: center; font-size: 4rem; margin-bottom: 10px;'>👤</div>", unsafe_allow_html=True)
                                            st.markdown(f"<div style='text-align: center;'><span style='font-size: 1.2rem; font-weight: 800; color: #09274e;'>{jugador.get('nombre')}</span><br><span style='font-size: 0.85rem; color: #64748b;'>{jugador.get('club_actual', 'Sin club')} | {jugador.get('categoria_actual', 'N/D')}</span></div>", unsafe_allow_html=True)
                                            st.markdown("<div style='height: 15px'></div>", unsafe_allow_html=True)
                                            if st.button("📁 Perfil", key=f"btn_perfil_{jugador.get('id')}", use_container_width=True):
                                                st.info(f"Vista de perfil de {jugador.get('nombre')} en desarrollo.")

# ==========================================
# PESTAÑA 2: REGISTRAR / RENOVAR DEPORTISTA
# ==========================================
with tab_nuevo:
    st.markdown("### 📝 Alta o Renovación de Deportista")
    st.info("💡 Si introduces un nombre que ya existe en la base de datos, el sistema **no creará un duplicado**, sino que añadirá esta nueva temporada a su historial (manteniendo sus valoraciones intactas).")
    
    with st.form("form_nuevo_jugador"):
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            nombre = st.text_input("Nombre y Apellidos (Exactos):")
            programa = st.selectbox("Programa (Esta Temporada):", options=lista_programas)
            
        with c2:
            club = st.text_input("Club (Esta Temporada):", placeholder="Ej: RC Celta...")
            categoria_club = st.text_input("Cat. Club (Esta Temporada):", placeholder="Ej: División de Honor...")
            
        with c3:
            categoria_edad = st.selectbox("Cat. de Edad (Esta Temporada):", options=lista_categorias)
            altura = st.number_input("Altura (cm):", min_value=100.0, max_value=220.0, value=170.0, step=0.5)

        with c4:
            pierna_dominante = st.selectbox("Pierna Dominante:", options=["Derecha", "Izquierda", "Ambidextra"])
            brazo_dominante = st.selectbox("Brazo Dominante:", options=["Derecho", "Izquierdo", "Ambidextro"])
            
        st.markdown("---")
        
        if st.form_submit_button(f"💾 Guardar/Renovar para {temp_vista}", use_container_width=True):
            nombre = nombre.strip()
            if not nombre:
                st.error("El nombre del deportista es obligatorio.")
            else:
                try:
                    # Buscar si el jugador ya existe (sin importar mayúsculas/minúsculas)
                    jugador_existente = next((j for j in jugadores if j['nombre'].lower() == nombre.lower()), None)
                    
                    datos_temporada_actual = {
                        "programa": programa,
                        "club": club.strip() if club else None,
                        "categoria_club": categoria_club.strip() if categoria_club else None,
                        "categoria_edad": categoria_edad
                    }

                    if jugador_existente:
                        # RENOVAR JUGADOR EXISTENTE
                        historial = jugador_existente.get('historial_temporadas', {})
                        if not isinstance(historial, dict): historial = {}
                        
                        historial[temp_vista] = datos_temporada_actual
                        
                        datos_update = {
                            "historial_temporadas": historial,
                            "altura": float(altura), # Actualizamos variables biológicas
                            "pierna_dominante": pierna_dominante,
                            "brazo_dominante": brazo_dominante
                        }
                        supabase.table("jugadores").update(datos_update).eq("id", jugador_existente['id']).execute()
                        st.success(f"¡El deportista '{nombre}' ya existía! Se ha actualizado su inscripción para la temporada {temp_vista}.")
                    else:
                        # CREAR NUEVO JUGADOR
                        nuevo_historial = {temp_vista: datos_temporada_actual}
                        nuevo_jugador = {
                            "nombre": nombre,
                            "altura": float(altura),
                            "pierna_dominante": pierna_dominante,
                            "brazo_dominante": brazo_dominante,
                            "historial_temporadas": nuevo_historial,
                            # Dejamos estos campos base por retrocompatibilidad con otras partes del código temporalmente
                            "programa": programa, 
                            "categoria_edad": categoria_edad
                        }
                        supabase.table("jugadores").insert(nuevo_jugador).execute()
                        st.success(f"¡Nuevo deportista '{nombre}' registrado correctamente para la {temp_vista}!")
                        
                    cargar_datos_sistema(force_refresh=True)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

# ==========================================
# PESTAÑA 3: MODIFICAR / ELIMINAR DEPORTISTA
# ==========================================
with tab_editar:
    st.markdown("### ✏️ Modificar o Eliminar")
    
    if not jugadores:
        st.info("No hay deportistas en la base de datos.")
    else:
        opciones_jugadores = {j['id']: f"{j.get('nombre')}" for j in jugadores}
        jugador_editar_id = st.selectbox("Selecciona al deportista:", options=list(opciones_jugadores.keys()), format_func=lambda x: opciones_jugadores[x])
        jugador_actual = next((j for j in jugadores if j['id'] == jugador_editar_id), None)
        
        if jugador_actual:
            historial_ed = jugador_actual.get('historial_temporadas', {})
            if not isinstance(historial_ed, dict): historial_ed = {}
            
            # Cogemos los datos de la temporada seleccionada arriba, si no, vacíos
            datos_temp_ed = historial_ed.get(temp_vista, {})
            
            with st.form("form_editar_jugador"):
                st.info(f"Editando los datos deportivos de **{temp_vista}** y biológicos generales.")
                ec1, ec2, ec3, ec4 = st.columns(4)
                
                with ec1:
                    e_nombre = st.text_input("Nombre y Apellidos:", value=jugador_actual.get('nombre', ''))
                    prog_act = datos_temp_ed.get('programa', jugador_actual.get('programa'))
                    idx_prog = lista_programas.index(prog_act) if prog_act in lista_programas else 0
                    e_programa = st.selectbox("Programa (En esta Temp):", options=lista_programas, index=idx_prog)
                    
                with ec2:
                    e_club = st.text_input("Club (En esta Temp):", value=datos_temp_ed.get('club', jugador_actual.get('club', '')))
                    e_categoria_club = st.text_input("Cat. Club (En esta Temp):", value=datos_temp_ed.get('categoria_club', jugador_actual.get('categoria_club', '')))
                    
                with ec3:
                    cat_act = datos_temp_ed.get('categoria_edad', jugador_actual.get('categoria_edad'))
                    idx_cat = lista_categorias.index(cat_act) if cat_act in lista_categorias else 0
                    e_categoria_edad = st.selectbox("Cat. Edad (En esta Temp):", options=lista_categorias, index=idx_cat)
                    e_altura = st.number_input("Altura (cm):", min_value=100.0, max_value=220.0, value=float(jugador_actual.get('altura', 170.0) or 170.0), step=0.5)

                with ec4:
                    pierna_act = jugador_actual.get('pierna_dominante')
                    idx_pierna = ["Derecha", "Izquierda", "Ambidextra"].index(pierna_act) if pierna_act in ["Derecha", "Izquierda", "Ambidextra"] else 0
                    e_pierna = st.selectbox("Pierna Dominante:", options=["Derecha", "Izquierda", "Ambidextra"], index=idx_pierna)
                    
                    brazo_act = jugador_actual.get('brazo_dominante')
                    idx_brazo = ["Derecho", "Izquierdo", "Ambidextro"].index(brazo_act) if brazo_act in ["Derecho", "Izquierdo", "Ambidextro"] else 0
                    e_brazo = st.selectbox("Brazo Dominante:", options=["Derecho", "Izquierdo", "Ambidextro"], index=idx_brazo)
                    
                st.markdown("---")
                
                if st.form_submit_button("🔄 Actualizar Datos", use_container_width=True):
                    if not e_nombre.strip(): st.error("El nombre no puede estar vacío.")
                    else:
                        try:
                            # Actualizamos el JSON solo para la temporada seleccionada
                            historial_ed[temp_vista] = {
                                "programa": e_programa,
                                "club": e_club.strip() if e_club else None,
                                "categoria_club": e_categoria_club.strip() if e_categoria_club else None,
                                "categoria_edad": e_categoria_edad
                            }
                            
                            datos_actualizados = {
                                "nombre": e_nombre.strip(),
                                "historial_temporadas": historial_ed,
                                "pierna_dominante": e_pierna,
                                "brazo_dominante": e_brazo,
                                "altura": float(e_altura),
                                # Mantenemos esto temporalmente para no romper los otros archivos
                                "programa": e_programa, 
                                "categoria_edad": e_categoria_edad 
                            }
                            
                            supabase.table("jugadores").update(datos_actualizados).eq("id", jugador_editar_id).execute()
                            cargar_datos_sistema(force_refresh=True)
                            st.success(f"¡Datos actualizados!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al actualizar: {e}")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Eliminar Deportista Definitivamente", type="primary", use_container_width=True):
                try:
                    supabase.table("jugadores").delete().eq("id", jugador_editar_id).execute()
                    cargar_datos_sistema(force_refresh=True)
                    st.success("¡Deportista eliminado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
