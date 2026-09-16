import streamlit as st
from database.db_manager import get_supabase_client, cargar_datos_sistema
from utils.math_helpers import aplicar_estilos_base
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Entrenamientos - ImpulseFootball", page_icon="📋", layout="wide")
aplicar_estilos_base()

supabase = get_supabase_client()

if not st.session_state.get("autenticado", False):
    st.warning("Sesión caducada.")
    st.stop()

cargar_datos_sistema()

st.title("📋 Control e Historial de Entrenamientos")

tab_historial, tab_faltas, tab_analitica = st.tabs([
    "🗓️ Historial y Modificación", 
    "⚠️ Gestión de Faltas", 
    "📊 Asistencias por Programa y Jugador"
])

jugadores = st.session_state.get("jugadores", [])
sesiones = st.session_state.get("sesiones", [])
lista_entrenadores = ["Entrenador Principal (Staff)", "Preparador Físico (PF)", "Segundo Entrenador", "Entrenador de Porteros"]

# ==========================================
# PESTAÑA 1: HISTORIAL Y MODIFICACIÓN DE SESIONES
# ==========================================
with tab_historial:
    st.markdown("### 🗓️ Registro Histórico y Edición de Sesiones")
    
    if not sesiones:
        st.info("Aún no hay sesiones registradas en el sistema.")
    else:
        # Selector de sesión a modificar
        opciones_sesiones = {s['id']: f"{s.get('fecha')} - {s.get('tipo', 'Sesión')} ({s.get('programa')}) - {s.get('hora_inicio', '')[:5]}" for s in sesiones}
        sesion_editar_id = st.selectbox("Selecciona una sesión para consultar o modificar:", options=list(opciones_sesiones.keys()), format_func=lambda x: opciones_sesiones[x])
        
        sesion_actual = next((s for s in sesiones if s['id'] == sesion_editar_id), None)
        
        if sesion_actual:
            with st.form("form_modificar_sesion"):
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    f_fecha = st.date_input("Fecha:", value=datetime.strptime(sesion_actual['fecha'], "%Y-%m-%d").date())
                    f_tipo = st.selectbox("Tipo:", options=["Campo", "Gimnasio"], index=0 if sesion_actual.get('tipo') == "Campo" else 1)
                with sc2:
                    hora_val = datetime.strptime(str(sesion_actual.get('hora_inicio', '17:00'))[:5], "%H:%M").time()
                    f_hora = st.time_input("Hora de Inicio:", value=hora_val)
                    ent_actual = sesion_actual.get('entrenador')
                    idx_ent = lista_entrenadores.index(ent_actual) if ent_actual in lista_entrenadores else 0
                    f_entrenador = st.selectbox("Entrenador:", options=lista_entrenadores, index=idx_ent)
                with sc3:
                    prog_actual = sesion_actual.get('programa')
                    list_progs = ["Academy", "Elite", "Promise", "OffSeason"]
                    idx_prog = list_progs.index(prog_actual) if prog_actual in list_progs else 0
                    f_programa = st.selectbox("Programa:", options=list_progs, index=idx_prog)
                
                f_comentarios = st.text_area("Foco de la Sesión / Observaciones:", value=sesion_actual.get('comentarios', ''))
                
                st.markdown("---")
                st.markdown("#### 👥 Jugadores Convocados y Asistentes")
                
                # Jugadores teóricos del programa
                jugadores_prog = [j['nombre'] for j in jugadores if j.get("programa") == f_programa]
                asistentes_previos = sesion_actual.get('asistentes', [])
                
                f_asistentes = st.multiselect(
                    "Selecciona los jugadores que acudieron realmente:",
                    options=jugadores_prog,
                    default=[a for a in asistentes_previos if a in jugadores_prog]
                )
                
                if st.form_submit_button("💾 Guardar Cambios en la Sesión", use_container_width=True):
                    try:
                        datos_actualizados = {
                            "fecha": str(f_fecha),
                            "hora_inicio": str(f_hora),
                            "tipo": f_tipo,
                            "programa": f_programa,
                            "entrenador": f_entrenador,
                            "asistentes": f_asistentes,
                            "comentarios": f_comentarios
                        }
                        supabase.table("sesiones_entrenamiento").update(datos_actualizados).eq("id", sesion_editar_id).execute()
                        cargar_datos_sistema(force_refresh=True)
                        st.success("¡Sesión actualizada correctamente!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al actualizar la sesión: {e}")

# ==========================================
# PESTAÑA 2: GESTIÓN DE FALTAS (NO PRESENTADOS)
# ==========================================
with tab_faltas:
    st.markdown("### ⚠️ Auditoría de Faltas e Inasistencias")
    st.info("💡 Aquí puedes ver rápidamente qué jugadores estaban previstos en un programa pero **no constan como asistentes** en las sesiones registradas.")
    
    if not sesiones or not jugadores:
        st.info("Faltan datos de sesiones o jugadores para realizar el análisis de faltas.")
    else:
        # Seleccionar sesión para auditar
        opciones_aud = {s['id']: f"{s.get('fecha')} - {s.get('programa')} ({s.get('tipo', 'Sesión')})" for s in sesiones}
        sesion_aud_id = st.selectbox("Selecciona la sesión a auditar:", options=list(opciones_aud.keys()), format_func=lambda x: opciones_aud[x], key="aud_sesion")
        
        sesion_a_revisar = next((s for s in sesiones if s['id'] == sesion_aud_id), None)
        
        if sesion_a_revisar:
            prog_sesion = sesion_a_revisar.get('programa')
            convocados_teoricos = [j['nombre'] for j in jugadores if j.get("programa") == prog_sesion]
            asistentes_reales = sesion_a_revisar.get('asistentes', [])
            
            faltaban = [j for j in convocados_teoricos if j not in asistentes_reales]
            
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                st.markdown(f"#### ✅ Asistentes ({len(asistentes_reales)})")
                for a in asistentes_reales:
                    st.write(f"- {a}")
            with c_f2:
                st.markdown(f"#### ❌ Ausencias / Faltas ({len(faltaban)})")
                if not faltaban:
                    st.success("¡Pleno de asistencia en esta sesión!")
                else:
                    for f in faltaban:
                        st.error(f"- {f} (Estaba convocado pero no asistió)")

# ==========================================
# PESTAÑA 3: ANALÍTICA DE ASISTENCIAS (PROGRAMA Y JUGADOR)
# ==========================================
with tab_analitica:
    st.markdown("### 📊 Estadísticas de Asistencia y Carga de Trabajo")
    
    if not sesiones or not jugadores:
        st.info("No hay suficientes datos para generar estadísticas.")
    else:
        # Filtro global de programa para la analítica
        filtro_prog_analitica = st.selectbox("Filtrar Programa:", options=["Todos", "Academy", "Elite", "Promise"], key="analitica_prog")
        
        sesiones_filtradas = sesiones if filtro_prog_analitica == "Todos" else [s for s in sesiones if s.get("programa") == filtro_prog_analitica]
        jugadores_filtrados = jugadores if filtro_prog_analitica == "Todos" else [j for j in jugadores if j.get("programa") == filtro_prog_analitica]
        
        total_sesiones_programa = len(sesiones_filtradas)
        
        st.metric(label=f"Total de Sesiones Registradas ({filtro_prog_analitica})", value=total_sesiones_programa)
        st.markdown("---")
        
        st.markdown("#### 👤 Resumen Individual por Deportista")
        
        if not jugadores_filtrados:
            st.warning("No hay jugadores en este programa.")
        else:
            datos_tabla_asistencia = []
            
            for j in jugadores_filtrados:
                nombre_j = j['nombre']
                # Contar a cuántas sesiones ha asistido
                asistencias_j = sum(1 for s in sesiones_filtradas if nombre_j in s.get('asistentes', []))
                porcentaje = round((asistencias_j / total_sesiones_programa * 100), 1) if total_sesiones_programa > 0 else 0.0
                
                datos_tabla_asistencia.append({
                    "Deportista": nombre_j,
                    "Programa": j.get('programa'),
                    "Categoría": j.get('categoria_edad', 'N/D'),
                    "Sesiones Totales": total_sesiones_programa,
                    "Asistencias": asistencias_j,
                    "Faltas": total_sesiones_programa - asistencias_j,
                    "% Adherencia": f"{porcentaje}%"
                })
                
            df_asistencias = pd.DataFrame(datos_tabla_asistencia)
            st.dataframe(df_asistencias, use_container_width=True, hide_index=True)
