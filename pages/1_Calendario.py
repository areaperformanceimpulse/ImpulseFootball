import streamlit as st
from database.db_manager import supabase, cargar_datos_sistema
from utils.math_helpers import aplicar_estilos_base
from datetime import date, datetime
import pandas as pd

st.set_page_config(page_title="Calendario - ImpulseFootball", page_icon="📅", layout="wide")
aplicar_estilos_base()

if not st.session_state.get("autenticado", False):
    st.warning("Sesión caducada.")
    st.stop()

cargar_datos_sistema()

st.title("📅 Calendario y Planificación de Sesiones")

tab_nueva, tab_visual, tab_historial = st.tabs(["➕ Programar Nueva Sesión", "🗓️ Vista Visual & Historial", "✏️ Modificar / Gestionar Sesión"])

jugadores = st.session_state.get("jugadores", [])
sesiones = st.session_state.get("sesiones", [])

# Lista simulada de entrenadores (puedes adaptarla a tu tabla de usuarios si la tienes)
lista_entrenadores = ["Entrenador Principal (Staff)", "Preparador Físico (PF)", "Segundo Entrenador", "Entrenador de Porteros"]

# ==========================================
# PESTAÑA 1: PROGRAMAR NUEVA SESIÓN
# ==========================================
with tab_nueva:
    st.markdown("### 📝 Configurar Sesión Semanal")
    
    if not jugadores:
        st.warning("No hay deportistas registrados en el sistema.")
    else:
        with st.form("form_nueva_sesion"):
            c1, c2, c3 = st.columns(3)
            
            with c1:
                fecha_sesion = st.date_input("Fecha del Entrenamiento:", value=date.today())
                hora_sesion = st.time_input("Hora de Inicio:", value=datetime.strptime("17:00", "%H:%M").time())
                tipo_sesion = st.selectbox("Tipo de Sesión:", options=["Campo", "Gimnasio"])
                
            with c2:
                programa_sel = st.selectbox("Programa de Entrenamiento:", options=["Academy", "Elite", "Promise"])
                entrenador_sel = st.selectbox("Entrenador Responsable:", options=lista_entrenadores)
                
                # Filtro dinámico de jugadores según el programa
                jugadores_filtrados = [j for j in jugadores if j.get("programa") == programa_sel]
                nombres_filtrados = [j["nombre"] for j in jugadores_filtrados]
                
            with c3:
                comentarios = st.text_area("Foco de la Sesión / Observaciones:", height=135, placeholder="Ej: Trabajo de fuerza explosiva y transiciones...")

            st.markdown("---")
            asistentes = st.multiselect(
                f"Deportistas Convocados ({len(nombres_filtrados)} disponibles en {programa_sel}):", 
                options=nombres_filtrados,
                default=nombres_filtrados # Por defecto todos los del grupo
            )
            
            submit_sesion = st.form_submit_button("💾 Guardar y Validar Sesión", use_container_width=True)
            
            if submit_sesion:
                if not asistentes:
                    st.error("Debes seleccionar al menos un deportista para la sesión.")
                else:
                    # VALIDACIÓN ANTI-SOLAPES DE ENTRENADOR
                    conflicto_entrenador = False
                    for s in sesiones:
                        if s.get("fecha") == str(fecha_sesion) and s.get("hora_inicio") == str(hora_sesion) and s.get("entrenador") == entrenador_sel:
                            conflicto_entrenador = True
                            break
                    
                    if conflicto_entrenador:
                        st.warning(f"⚠️ **Aviso de Solape:** El entrenador '{entrenador_sel}' ya tiene asignada otra sesión el {fecha_sesion} a las {hora_sesion}. La sesión se guardará igualmente, revísalo si es necesario.")
                    
                    try:
                        nueva_sesion = {
                            "fecha": str(fecha_sesion),
                            "hora_inicio": str(hora_sesion),
                            "tipo": tipo_sesion,
                            "programa": programa_sel,
                            "entrenador": entrenador_sel,
                            "asistentes": asistentes,
                            "comentarios": comentarios
                        }
                        supabase.table("sesiones_entrenamiento").insert(nueva_sesion).execute()
                        cargar_datos_sistema()
                        st.success(f"¡Sesión de {tipo_sesion} programada correctamente para el {fecha_sesion} a las {hora_sesion}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar la sesión: {e}")

# ==========================================
# PESTAÑA 2: VISTA VISUAL & HISTORIAL
# ==========================================
with tab_visual:
    st.markdown("### 🗓️ Parrilla de Sesiones Programadas")
    
    if not sesiones:
        st.info("Aún no hay sesiones registradas en el calendario.")
    else:
        df_sesiones = pd.DataFrame(sesiones)
        df_sesiones = df_sesiones.sort_values(by=["fecha", "hora_inicio"], ascending=[False, True])
        
        # Filtros de visualización rápidos
        fc1, fc2, fc3 = st.columns(3)
        with fc1: filtro_prog = st.selectbox("Filtrar Programa:", ["Todos", "Academy", "Elite", "Promise"], key="f_prog")
        with fc2: filtro_tipo = st.selectbox("Filtrar Tipo:", ["Todos", "Campo", "Gimnasio"], key="f_tipo")
        with fc3: filtro_ent = st.selectbox("Filtrar Entrenador:", ["Todos"] + lista_entrenadores, key="f_ent")
        
        if filtro_prog != "Todos": df_sesiones = df_sesiones[df_sesiones["programa"] == filtro_prog]
        if filtro_tipo != "Todos": df_sesiones = df_sesiones[df_sesiones["tipo"] == filtro_tipo]
        if filtro_ent != "Todos": df_sesiones = df_sesiones[df_sesiones["entrenador"] == filtro_ent]
        
        st.markdown("---")
        
        if df_sesiones.empty:
            st.warning("No hay sesiones que coincidan con los filtros seleccionados.")
        else:
            for idx, row in df_sesiones.iterrows():
                tipo_icono = "⚽" if row.get("tipo") == "Campo" else "🏋️‍♂️"
                hora_str = str(row.get('hora_inicio', '00:00'))[:5]
                
                with st.expander(f"{tipo_icono} [{row.get('fecha')} - {hora_str}] Grupo: {row.get('programa')} | Dirige: {row.get('entrenador', 'No asignado')} ({len(row.get('asistentes', []))} asistentes)"):
                    cd1, cd2 = st.columns([2, 1])
                    with cd1:
                        st.markdown(f"**Tipo de Sesión:** {row.get('tipo', 'No especificado')}")
                        st.markdown(f"**📝 Foco / Observaciones:**")
                        st.write(row.get("comentarios") if row.get("comentarios") else "Sin observaciones registradas.")
                    with cd2:
                        st.markdown("**👥 Deportistas Convocados:**")
                        for jugador in row.get("asistentes", []):
                            st.write(f"- {jugador}")

# ==========================================
# PESTAÑA 3: MODIFICAR / GESTIONAR SESIÓN (FALTAS Y DATOS)
# ==========================================
with tab_historial:
    st.markdown("### ✏️ Modificar Sesión y Gestión de Faltas")
    
    if not sesiones:
        st.info("No hay sesiones para modificar.")
    else:
        # Seleccionar sesión a editar
        opciones_sesiones = {s['id']: f"{s.get('fecha')} - {s.get('tipo')} ({s.get('programa')})" for s in sesiones}
        sesion_editar_id = st.selectbox("Selecciona la sesión a modificar:", options=list(opciones_sesiones.keys()), format_func=lambda x: opciones_sesiones[x])
        
        sesion_actual = next((s for s in sesiones if s['id'] == sesion_editar_id), None)
        
        if sesion_actual:
            with st.form("form_editar_sesion"):
                ec1, ec2, ec3 = st.columns(3)
                with ec1:
                    e_fecha = st.date_input("Fecha:", value=datetime.strptime(sesion_actual['fecha'], "%Y-%m-%d").date())
                    e_tipo = st.selectbox("Tipo:", options=["Campo", "Gimnasio"], index=0 if sesion_actual.get('tipo') == "Campo" else 1)
                with ec2:
                    hora_val = datetime.strptime(str(sesion_actual.get('hora_inicio', '17:00'))[:5], "%H:%M").time()
                    e_hora = st.time_input("Hora de Inicio:", value=hora_val)
                    e_entrenador = st.selectbox("Entrenador:", options=lista_entrenadores, index=lista_entrenadores.index(sesion_actual.get('entrenador')) if sesion_actual.get('entrenador') in lista_entrenadores else 0)
                with ec3:
                    e_prog = st.selectbox("Programa:", options=["Academy", "Elite", "Promise"], index=["Academy", "Elite", "Promise"].index(sesion_actual.get('programa')) if sesion_actual.get('programa') in ["Academy", "Elite", "Promise"] else 0)
                
                e_comentarios = st.text_area("Foco de la Sesión:", value=sesion_actual.get('comentarios', ''))
                
                st.markdown("---")
                st.markdown("#### 👥 Gestión de Asistencias y Faltas")
                st.info("💡 Desmarca de la lista a los jugadores que finalmente **faltaron** a la sesión a pesar de estar convocados.")
                
                # Lista de jugadores totales del programa de esta sesión
                jugadores_prog = [j['nombre'] for j in jugadores if j.get("programa") == e_prog]
                asistentes_previos = sesion_actual.get('asistentes', [])
                
                e_asistentes = st.multiselect(
                    "Deportistas asistentes reales:",
                    options=jugadores_prog,
                    default=[a for a in asistentes_previos if a in jugadores_prog]
                )
                
                if st.form_submit_button("🔄 Actualizar Datos de Sesión", use_container_width=True):
                    try:
                        datos_actualizados = {
                            "fecha": str(e_fecha),
                            "hora_inicio": str(e_hora),
                            "tipo": e_tipo,
                            "programa": e_prog,
                            "entrenador": e_entrenador,
                            "asistentes": e_asistentes,
                            "comentarios": e_comentarios
                        }
                        supabase.table("sesiones_entrenamiento").update(datos_actualizados).eq("id", sesion_editar_id).execute()
                        cargar_datos_sistema()
                        st.success("¡Sesión actualizada correctamente con la gestión de asistencias!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al actualizar la sesión: {e}")
