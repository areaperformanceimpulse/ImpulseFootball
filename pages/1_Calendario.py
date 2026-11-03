import streamlit as st
from database.db_manager import get_supabase_client, cargar_datos_sistema
from utils.math_helpers import aplicar_estilos_base
from datetime import date, datetime
import pandas as pd

st.set_page_config(page_title="Calendario", page_icon="📅", layout="wide")
aplicar_estilos_base()

supabase = get_supabase_client()

if not st.session_state.get("autenticado", False):
    st.warning("Sesión caducada.")
    st.stop()

cargar_datos_sistema()

st.title("📅 Calendario y Planificación de Sesiones")

# NUEVO ORDEN DE PESTAÑAS
tab_calendario, tab_nueva, tab_historial = st.tabs(["📅 Calendario Mensual", "➕ Programar Nueva Sesión", "✏️ Modificar / Gestionar Sesión"])

jugadores = st.session_state.get("jugadores", [])
sesiones = st.session_state.get("sesiones", [])

# ==========================================
# PESTAÑA 1: PROGRAMAR NUEVA SESIÓN
# ==========================================
with tab_nueva:
    st.markdown("### 📝 Configurar Sesión Semanal")
    
    if not jugadores:
        st.warning("No hay deportistas registrados en el sistema.")
    else:
        c1, c2 = st.columns(2)
        
        with c1:
            fecha_sesion = st.date_input("Fecha del Entrenamiento:", value=date.today())
            hora_sesion = st.time_input("Hora de Inicio:", value=datetime.strptime("17:00", "%H:%M").time())
            tipo_sesion = st.selectbox("Tipo de Sesión:", options=["Campo", "Gimnasio"])
            
        with c2:
            programa_sel = st.selectbox("Programa de Entrenamiento:", options=["Academy", "Elite", "Promise", "OffSeason"])
            jugadores_filtrados = [j for j in jugadores if j.get("programa") == programa_sel]
            nombres_filtrados = [j["nombre"] for j in jugadores_filtrados]

        st.markdown("---")
        asistentes = st.multiselect(
            f"Deportistas Convocados ({len(nombres_filtrados)} disponibles en {programa_sel}):", 
            options=nombres_filtrados,
            default=nombres_filtrados
        )
        
        st.markdown("")
        if st.button("💾 Guardar Sesión", use_container_width=True):
            if not asistentes:
                st.error("Debes seleccionar al menos un deportista para la sesión.")
            else:
                try:
                    nueva_sesion = {
                        "usuario_id": st.session_state.get("usuario_id"), # VINCULACIÓN DE SEGURIDAD
                        "fecha": str(fecha_sesion),
                        "hora_inicio": str(hora_sesion),
                        "tipo": tipo_sesion,
                        "programa": programa_sel,
                        "asistentes": asistentes,
                        "comentarios": ""
                    }
                    supabase.table("sesiones_entrenamiento").insert(nueva_sesion).execute()
                    cargar_datos_sistema(force_refresh=True)
                    st.success(f"¡Sesión de {tipo_sesion} programada correctamente para el {fecha_sesion}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar la sesión: {e}")

# ==========================================
# PESTAÑA 2: VISTA VISUAL & HISTORIAL
# ==========================================
with tab_calendario:
    st.markdown("### 📅 Vista Mensual de Sesiones")
    
    if not sesiones:
        st.info("Aún no hay sesiones registradas.")
    else:
        import calendar
        hoy = date.today()
        
        c_mes1, c_mes2, c_mes3 = st.columns([1, 2, 1])
        with c_mes2:
            mes_sel = st.selectbox("Mes:", range(1, 13), index=hoy.month - 1, format_func=lambda x: calendar.month_name[x].capitalize())
            año_sel = st.selectbox("Año:", range(hoy.year - 1, hoy.year + 2), index=1)
            
        df_sesiones = pd.DataFrame(sesiones)
        df_sesiones['fecha'] = pd.to_datetime(df_sesiones['fecha'])
        df_mes = df_sesiones[(df_sesiones['fecha'].dt.month == mes_sel) & (df_sesiones['fecha'].dt.year == año_sel)]
        
        st.markdown("---")
        cal = calendar.monthcalendar(año_sel, mes_sel)
        dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        
        # Cabecera días
        cols_dias = st.columns(7)
        for i, dia in enumerate(dias_semana):
            cols_dias[i].markdown(f"<div style='text-align: center; font-weight: 800; color: #64748b;'>{dia}</div>", unsafe_allow_html=True)
            
        # Generación de la cuadrícula
        for semana in cal:
            cols = st.columns(7)
            for i, dia in enumerate(semana):
                with cols[i]:
                    if dia != 0:
                        sesiones_dia = df_mes[df_mes['fecha'].dt.day == dia]
                        fondo = "#f8fafc" if sesiones_dia.empty else "#eef2ff"
                        borde = "#e2e8f0" if sesiones_dia.empty else "#10833d"
                        
                        html_dia = f"<div style='background-color: {fondo}; border: 1px solid {borde}; border-radius: 8px; padding: 10px; min-height: 100px; margin-bottom: 10px;'>"
                        html_dia += f"<div style='font-weight: 800; font-size: 1.1em; color: #09274e;'>{dia}</div>"
                        
                        for _, s in sesiones_dia.iterrows():
                            icono = "⚽" if s.get('tipo') == 'Campo' else "🏋️"
                            hora = str(s.get('hora_inicio', ''))[:5]
                            html_dia += f"<div style='font-size: 0.75em; background: white; padding: 4px; border-radius: 4px; margin-top: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);'><b>{hora}</b> {icono} {s.get('programa')}</div>"
                            
                        html_dia += "</div>"
                        st.markdown(html_dia, unsafe_allow_html=True)

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
                with ec3:
                    e_prog = st.selectbox("Programa:", options=["Academy", "Elite", "Promise", "OffSeason"], index=["Academy", "Elite", "Promise", "OffSeason"].index(sesion_actual.get('programa')) if sesion_actual.get('programa') in ["Academy", "Elite", "Promise", "OffSeason"] else 0)
                               
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
                            "asistentes": e_asistentes,
                            "comentarios": "" # Lo mantenemos vacío en BD para no romper esquemas antiguos
                        }
                        supabase.table("sesiones_entrenamiento").update(datos_actualizados).eq("id", sesion_editar_id).execute()
                        cargar_datos_sistema(force_refresh=True)
                        st.success("¡Sesión actualizada correctamente con la gestión de asistencias!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al actualizar la sesión: {e}")
