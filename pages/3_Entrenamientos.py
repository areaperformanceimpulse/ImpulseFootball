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

st.title("📋 Análisis y Planificación de Entrenamientos")

# Solo mantenemos Analítica e IA (eliminando Historial y Faltas redundantes)
tab_analitica, tab_planificacion = st.tabs([
    "📊 Analítica de Asistencia", 
    "🧠 Planificación Inteligente"
])

jugadores = st.session_state.get("jugadores", [])
sesiones = st.session_state.get("sesiones", [])

# ==========================================
# PESTAÑA 1: ANALÍTICA DE ASISTENCIAS 
# ==========================================
with tab_analitica:
    st.markdown("### 📊 Estadísticas de Asistencia y Carga de Trabajo")
    
    if not sesiones or not jugadores:
        st.info("No hay suficientes datos para generar estadísticas.")
    else:
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
                
                # Calcular en cuántas sesiones estuvo convocado
                sesiones_convocado = sum(1 for s in sesiones_filtradas if nombre_j in s.get('convocados', s.get('asistentes', [])))
                
                if sesiones_convocado > 0:
                    # Calcular a cuántas asistió realmente
                    asistencias_j = sum(1 for s in sesiones_filtradas if nombre_j in s.get('asistentes', []))
                    porcentaje = round((asistencias_j / sesiones_convocado * 100), 1)
                    
                    datos_tabla_asistencia.append({
                        "Deportista": nombre_j,
                        "Programa": j.get('programa'),
                        "Convocatorias": sesiones_convocado,
                        "Asistencias": asistencias_j,
                        "Faltas": sesiones_convocado - asistencias_j,
                        "% Adherencia": f"{porcentaje}%"
                    })
                
            df_asistencias = pd.DataFrame(datos_tabla_asistencia)
            if not df_asistencias.empty:
                st.dataframe(df_asistencias, use_container_width=True, hide_index=True)
            else:
                st.info("Aún no hay convocatorias registradas para los deportistas de este grupo.")

# ==========================================
# PESTAÑA 2: PLANIFICACIÓN MENSUAL E INTELIGENCIA ARTIFICIAL
# ==========================================
with tab_planificacion:
    st.markdown("### 🧠 Planificador de Contenidos y Motor IA")
    st.info("Diseña los mesociclos y extrae propuestas de tareas basadas en las últimas métricas condicionales de los deportistas.")
    
    cp1, cp2 = st.columns([1, 2])
    with cp1:
        prog_plan = st.selectbox("Selecciona Programa:", ["Academy", "Elite", "Promise", "OffSeason"], key="prog_plan")
        jugadores_prog = [j['nombre'] for j in jugadores if j.get('programa') == prog_plan]
        objetivo_mensual = st.text_area("Objetivos Condicionales del Mesociclo:", height=150, placeholder="Ej: Énfasis en fuerza excéntrica isquiosural y vectores horizontales...")
        
        st.markdown("---")
        st.markdown("#### 🤖 Asistente IA (Generador de Sesiones)")
        atleta_target = st.selectbox("Analizar y generar para:", ["Grupo Completo"] + jugadores_prog)
        
        if st.button("✨ Generar Planificación con IA", type="primary", use_container_width=True):
            st.warning("Motor IA en preparación. (Requiere inyectar API Key en st.secrets).")
            
    with cp2:
        st.markdown("#### 📝 Pizarra de Contenidos (Borrador)")
        contenido_borrador = st.text_area("Desarrollo de las sesiones (Semanas 1 a 4):", height=400, placeholder="Semana 1:\n- Sesión Campo (Fuerza Específica):\n- Sesión Gimnasio (Potencia):\n\nSemana 2...")
        
        if st.button("💾 Guardar Borrador de Planificación", use_container_width=True):
            st.success("Borrador guardado temporalmente. (Para persistencia crearemos la tabla 'planificaciones_mensuales' en Supabase).")
