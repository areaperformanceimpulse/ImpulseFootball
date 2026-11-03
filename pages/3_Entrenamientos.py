import streamlit as st
from database.db_manager import get_supabase_client, cargar_datos_sistema
from utils.math_helpers import aplicar_estilos_base
from datetime import datetime
import pandas as pd
from datetime import datetime, date, timedelta

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
    st.markdown("### 🧠 Visor de Microciclo y Diseño de Sesiones")
    
    # --- GESTIÓN DE ESTADOS (Navegación y Selección) ---
    if "semana_offset" not in st.session_state: st.session_state.semana_offset = 0
    if "sesion_activa_id" not in st.session_state: st.session_state.sesion_activa_id = None

    # Cerrar el lienzo de sesión
    def cerrar_lienzo(): st.session_state.sesion_activa_id = None
    
    # --- CÁLCULO DE FECHAS DE LA SEMANA ---
    hoy = date.today()
    inicio_semana_actual = hoy - timedelta(days=hoy.weekday()) # Lunes
    lunes_visor = inicio_semana_actual + timedelta(weeks=st.session_state.semana_offset)
    domingo_visor = lunes_visor + timedelta(days=6)

    # ==========================================
    # VISTA 1: LIENZO DE DISEÑO DE SESIÓN (Detalle)
    # ==========================================
    if st.session_state.sesion_activa_id:
        s_activa = next((s for s in sesiones if s['id'] == st.session_state.sesion_activa_id), None)
        if not s_activa:
            st.session_state.sesion_activa_id = None
            st.rerun()
            
        st.button("⬅️ Volver a la Vista Semanal", on_click=cerrar_lienzo)
        st.markdown(f"#### 📝 Diseño de Sesión: {s_activa.get('programa')} ({s_activa.get('fecha')} - {str(s_activa.get('hora_inicio', ''))[:5]})")
        
        with st.form("form_diseno_sesion"):
            # 1. Variables de Sesión
            st.markdown("**1. Parámetros de Carga y Contexto**")
            cv1, cv2, cv3 = st.columns([1, 1, 2])
            with cv1: e_md = st.selectbox("Día de Competición (MD):", ["-", "MD-5", "MD-4", "MD-3", "MD-2", "MD-1", "MD", "MD+1", "MD+2"], index=["-", "MD-5", "MD-4", "MD-3", "MD-2", "MD-1", "MD", "MD+1", "MD+2"].index(s_activa.get('etiqueta_md', '-')))
            with cv2: e_rpe = st.number_input("RPE Estimado (1-10):", min_value=0, max_value=10, value=int(s_activa.get('rpe_estimado', 0)))
            with cv3: e_objetivo = st.text_input("Objetivo Principal de la Sesión:", value=s_activa.get('objetivo', ''), placeholder="Ej: Fuerza-Tensión (Cadenas posteriores y frenadas)")

            # Resumen de asistencia
            conv = s_activa.get('convocados', s_activa.get('asistentes', []))
            asist = s_activa.get('asistentes', [])
            faltas = [c for c in conv if c not in asist]
            txt_asistencia = f"👥 **Convocados:** {len(conv)} | ❌ **Ausencias:** {', '.join(faltas) if faltas else 'Ninguna'}"
            st.info(txt_asistencia)
            
            st.markdown("---")
            
            # 2. IA Generator
            st.markdown("**2. Asistente IA (Motor de Generación a 60')**")
            st.caption("🤖 Escanea el perfil biomecánico de los convocados y diseña tareas para compensar sus déficits y cumplir el objetivo.")
            
            btn_ia = st.form_submit_button("✨ Diseñar Sesión con Inteligencia Artificial", type="secondary", use_container_width=True)
            
            if btn_ia:
                if not e_objetivo:
                    st.error("⚠️ Define primero el 'Objetivo Principal de la Sesión' para dar contexto a la IA.")
                else:
                    with st.spinner("🧠 Analizando datos condicionales y estructurando tareas..."):
                        import google.generativeai as genai
                        import json
                        
                        try:
                            # 1. Extracción de datos biomecánicos
                            perfiles_clinicos = []
                            for nombre in conv:
                                jug = next((j for j in jugadores if j['nombre'] == nombre), None)
                                if jug:
                                    vals = [v for v in st.session_state.get("valoraciones", []) if v['jugador_id'] == jug['id']]
                                    if vals:
                                        u_val = sorted(vals, key=lambda x: x['fecha'], reverse=True)[0]
                                        ctrl_motor = u_val.get('fms_sentadilla', 0) + u_val.get('fms_estabilidad_tronco', 0)
                                        asi_cmj = abs(float(u_val.get('cmj_uni_der', 0)) - float(u_val.get('cmj_uni_izq', 0)))
                                        asi_isq = abs(float(u_val.get('iso_flex_rodilla_der', 0)) - float(u_val.get('iso_flex_rodilla_izq', 0)))
                                        perfiles_clinicos.append(f"- {nombre} | Control FMS (Core/SQ): {ctrl_motor}/6 | Asimetría CMJ: {asi_cmj}cm | Asimetría Isquios: {asi_isq}N")
                            
                            contexto_jugadores = "\n".join(perfiles_clinicos) if perfiles_clinicos else "Sin valoraciones registradas para estos deportistas."

                            # 2. Configuración Estricta de la API
                            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                            
                            # Ruta absoluta obligatoria
                            model = genai.GenerativeModel('models/gemini-3.8-flash')
                            
                            # 3. Prompting de Élite
                            prompt = f"""
                            Actúa como un Preparador Físico de Élite especializado en fútbol profesional y Microciclo Estructurado.
                            Diseña una sesión de 60 minutos basada en:
                            
                            - Contexto: {e_md}
                            - RPE Objetivo: {e_rpe}/10
                            - Objetivo: {e_objetivo}
                            - Perfiles Biomecánicos (Focaliza las tareas en compensar estos déficits):
                            {contexto_jugadores}

                            ESTRUCTURA EXACTA DEL JSON REQUERIDO:
                            {{
                                "activacion": "Pautas (10-15'). Ejercicios, series, repeticiones.",
                                "core": "Estabilidad (10'). Ejercicios, series, tiempos de tensión.",
                                "principal": "Fase principal (35-40'). Series, repeticiones, %RM o VBT, descansos."
                            }}
                            """
                            
                            # 4. Llamada con TIMEOUT AMPLIADO (60s) y MODO JSON NATIVO
                            res = model.generate_content(
                                prompt,
                                generation_config={"response_mime_type": "application/json"},
                                request_options={"timeout": 60.0}
                            )
                            
                            # 5. Parseo y guardado directo (el modo JSON nativo garantiza la estructura)
                            sesion_ia = json.loads(res.text)
                            
                            supabase.table("sesiones_entrenamiento").update({
                                "activacion": sesion_ia.get("activacion", ""),
                                "core": sesion_ia.get("core", ""),
                                "principal": sesion_ia.get("principal", ""),
                                "etiqueta_md": e_md,
                                "rpe_estimado": e_rpe,
                                "objetivo": e_objetivo
                            }).eq("id", s_activa['id']).execute()
                            
                            from database.db_manager import cargar_datos_sistema
                            cargar_datos_sistema(force_refresh=True)
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error técnico o Timeout al generar la sesión: {str(e)}")
            
            # 3. Estructura de la sesión
            st.markdown("**3. Estructura de Tareas**")
            e_activacion = st.text_area("Fase 1: Activación y Movilidad (10-15')", value=s_activa.get('activacion', ''), height=100)
            e_core = st.text_area("Fase 2: Core y Estabilidad (10')", value=s_activa.get('core', ''), height=100)
            e_principal = st.text_area("Fase 3: Parte Principal (Fuerza/Potencia/Campo) (35-40')", value=s_activa.get('principal', ''), height=150)
            
            if st.form_submit_button("💾 Guardar Diseño de Sesión", use_container_width=True):
                try:
                    datos_diseno = {
                        "etiqueta_md": e_md, "rpe_estimado": e_rpe, "objetivo": e_objetivo,
                        "activacion": e_activacion, "core": e_core, "principal": e_principal
                    }
                    supabase.table("sesiones_entrenamiento").update(datos_diseno).eq("id", s_activa['id']).execute()
                    from database.db_manager import cargar_datos_sistema
                    cargar_datos_sistema(force_refresh=True)
                    st.success("Diseño guardado correctamente.")
                    st.session_state.sesion_activa_id = None # Cierra y vuelve al calendario
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

    # ==========================================
    # VISTA 2: VISOR SEMANAL (Microciclo)
    # ==========================================
    else:
        cn1, cn2, cn3 = st.columns([1, 3, 1])
        with cn1: 
            if st.button("⬅️ Semana Anterior", use_container_width=True): 
                st.session_state.semana_offset -= 1
                st.rerun()
        with cn2: 
            st.markdown(f"<h4 style='text-align: center; color: #09274e;'>Microciclo: {lunes_visor.strftime('%d %b')} al {domingo_visor.strftime('%d %b %Y')}</h4>", unsafe_allow_html=True)
        with cn3: 
            if st.button("Semana Siguiente ➡️", use_container_width=True): 
                st.session_state.semana_offset += 1
                st.rerun()

        st.markdown("---")
        
        # Generar Grid Semanal
        dias_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        cols_dias = st.columns(7)
        
        df_sesiones = pd.DataFrame(sesiones)
        if not df_sesiones.empty:
            df_sesiones['fecha_dt'] = pd.to_datetime(df_sesiones['fecha']).dt.date
        
        for i in range(7):
            fecha_col = lunes_visor + timedelta(days=i)
            with cols_dias[i]:
                # Cabecera de día
                is_today = fecha_col == hoy
                bg_color = "#10833d" if is_today else "#f8fafc"
                text_color = "white" if is_today else "#64748b"
                st.markdown(f"<div style='background-color: {bg_color}; color: {text_color}; text-align: center; padding: 5px; border-radius: 5px; font-weight: 800; font-size: 0.9em; margin-bottom: 10px;'>{dias_nombres[i]}<br>{fecha_col.strftime('%d')}</div>", unsafe_allow_html=True)
                
                # Cargar tarjetas de sesión
                if not df_sesiones.empty:
                    sesiones_dia = df_sesiones[df_sesiones['fecha_dt'] == fecha_col]
                    for _, s in sesiones_dia.iterrows():
                        icono_tipo = "⚽" if s.get('tipo') == "Campo" else "🏋️"
                        md_tag = s.get('etiqueta_md', '-')
                        md_badge = f"<span style='background-color: #09274e; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.7em;'>{md_tag}</span>" if md_tag != '-' else ""
                        
                        html_card = f"""
                        <div style='border: 1px solid #e2e8f0; border-left: 4px solid #10833d; border-radius: 6px; padding: 8px; margin-bottom: 8px; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'>
                            <div style='font-size: 0.75em; color: #64748b; font-weight: 800;'>{str(s.get('hora_inicio', ''))[:5]} {icono_tipo} {md_badge}</div>
                            <div style='font-size: 0.9em; font-weight: 700; color: #09274e; margin-top: 4px;'>{s.get('programa')}</div>
                            <div style='font-size: 0.75em; color: #64748b; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>{s.get('objetivo', 'Sin objetivo definido')}</div>
                        </div>
                        """
                        st.markdown(html_card, unsafe_allow_html=True)
                        if st.button("✏️ Diseñar", key=f"btn_diseno_{s['id']}", use_container_width=True):
                            st.session_state.sesion_activa_id = s['id']
                            st.rerun()
