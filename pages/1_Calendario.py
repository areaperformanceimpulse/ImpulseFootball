import streamlit as st
from database.db_manager import get_supabase_client, cargar_datos_sistema
from utils.math_helpers import aplicar_estilos_base
from datetime import date, datetime
import pandas as pd
from datetime import date, datetime, timedelta
import calendar

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
    st.markdown("### 📝 Configurar Sesión")
    
    if not jugadores:
        st.warning("No hay deportistas registrados en el sistema.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        
        with c1: fecha_sesion = st.date_input("Fecha:", value=date.today())
        with c2: hora_sesion = st.time_input("Hora:", value=datetime.strptime("17:00", "%H:%M").time())
        with c3: tipo_sesion = st.selectbox("Tipo:", options=["Campo", "Gimnasio"])
        with c4: programa_sel = st.selectbox("Programa:", options=["Academy", "Elite", "Promise", "OffSeason"])
        
        jugadores_filtrados = [j for j in jugadores if j.get("programa") == programa_sel]
        nombres_filtrados = [j["nombre"] for j in jugadores_filtrados]

        st.markdown("---")
        asistentes = st.multiselect(
            f"Deportistas Convocados ({len(nombres_filtrados)} disponibles en {programa_sel}):", 
            options=nombres_filtrados,
            default=[] # Se inicia en blanco obligatoriamente
        )
        
        repetir_semanal = st.checkbox("🔄 Hacer esta sesión recurrente (Repetir semanalmente durante 4 semanas)")
        
        st.markdown("")
        if st.button("💾 Guardar Sesión", use_container_width=True):
            if not asistentes:
                st.error("Debes convocar al menos un deportista para la sesión.")
            else:
                try:
                    sesiones_a_guardar = []
                    semanas = 4 if repetir_semanal else 1
                    
                    for i in range(semanas):
                        fecha_iter = fecha_sesion + timedelta(days=7*i)
                        sesiones_a_guardar.append({
                            "usuario_id": st.session_state.get("usuario_id"),
                            "fecha": str(fecha_iter),
                            "hora_inicio": str(hora_sesion),
                            "tipo": tipo_sesion,
                            "programa": programa_sel,
                            "asistentes": asistentes,
                            "comentarios": ""
                        })
                        
                    supabase.table("sesiones_entrenamiento").insert(sesiones_a_guardar).execute()
                    cargar_datos_sistema(force_refresh=True)
                    msg = "¡Sesión programada!" if not repetir_semanal else "¡Sesiones recurrentes (4 semanas) programadas!"
                    st.success(f"{msg} Correctamente.")
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
        # Inicializar estado del calendario si no existe
        if "cal_fecha" not in st.session_state:
            st.session_state.cal_fecha = date.today().replace(day=1)
            
        c_nav1, c_nav2, c_nav3 = st.columns([1, 4, 1])
        with c_nav1:
            if st.button("⬅️ Mes Anterior", use_container_width=True):
                mes_ant = st.session_state.cal_fecha.month - 1
                año_ant = st.session_state.cal_fecha.year
                if mes_ant == 0: mes_ant, año_ant = 12, año_ant - 1
                st.session_state.cal_fecha = date(año_ant, mes_ant, 1)
                st.rerun()
        with c_nav2:
            mes_str = calendar.month_name[st.session_state.cal_fecha.month].capitalize()
            st.markdown(f"<h4 style='text-align: center; margin-top: 0; color: #09274e;'>{mes_str} {st.session_state.cal_fecha.year}</h4>", unsafe_allow_html=True)
        with c_nav3:
            if st.button("Mes Siguiente ➡️", use_container_width=True):
                mes_sig = st.session_state.cal_fecha.month + 1
                año_sig = st.session_state.cal_fecha.year
                if mes_sig == 13: mes_sig, año_sig = 1, año_sig + 1
                st.session_state.cal_fecha = date(año_sig, mes_sig, 1)
                st.rerun()
                
        df_sesiones = pd.DataFrame(sesiones)
        df_sesiones['fecha_dt'] = pd.to_datetime(df_sesiones['fecha'])
        df_mes = df_sesiones[(df_sesiones['fecha_dt'].dt.month == st.session_state.cal_fecha.month) & (df_sesiones['fecha_dt'].dt.year == st.session_state.cal_fecha.year)]
        
        st.markdown("---")
        cal = calendar.monthcalendar(st.session_state.cal_fecha.year, st.session_state.cal_fecha.month)
        dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        
        cols_dias = st.columns(7)
        for i, dia in enumerate(dias_semana):
            cols_dias[i].markdown(f"<div style='text-align: center; font-weight: 800; color: #64748b;'>{dia}</div>", unsafe_allow_html=True)
            
        for semana in cal:
            cols = st.columns(7)
            for i, dia in enumerate(semana):
                with cols[i]:
                    if dia != 0:
                        sesiones_dia = df_mes[df_mes['fecha_dt'].dt.day == dia]
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
        def format_titulo(s):
            asist = s.get('asistentes', [])
            if s.get('tipo') == 'Campo' and len(asist) >= 5:
                titulo = f"Campo: {s.get('programa')}"
            else:
                nombres = ", ".join(asist) if asist else "Sin convocados"
                if len(nombres) > 40: nombres = nombres[:37] + "..."
                titulo = f"Gimnasio: {nombres}" if s.get('tipo') == 'Gimnasio' else f"Campo: {nombres}"
            return f"{s.get('fecha')} | {titulo} ({str(s.get('hora_inicio', ''))[:5]})"

        opciones_sesiones = {s['id']: format_titulo(s) for s in sesiones}
        sesion_editar_id = st.selectbox("Selecciona la sesión a gestionar:", options=list(opciones_sesiones.keys()), format_func=lambda x: opciones_sesiones[x])
        
        sesion_actual = next((s for s in sesiones if s['id'] == sesion_editar_id), None)
        
        if sesion_actual:
            with st.form("form_editar_sesion"):
                ec1, ec2, ec3, ec4 = st.columns(4)
                with ec1: e_fecha = st.date_input("Fecha:", value=datetime.strptime(sesion_actual['fecha'], "%Y-%m-%d").date())
                with ec2: e_hora = st.time_input("Hora:", value=datetime.strptime(str(sesion_actual.get('hora_inicio', '17:00'))[:5], "%H:%M").time())
                with ec3: e_tipo = st.selectbox("Tipo:", options=["Campo", "Gimnasio"], index=0 if sesion_actual.get('tipo') == "Campo" else 1)
                with ec4: e_prog = st.selectbox("Programa:", options=["Academy", "Elite", "Promise", "OffSeason"], index=["Academy", "Elite", "Promise", "OffSeason"].index(sesion_actual.get('programa')) if sesion_actual.get('programa') in ["Academy", "Elite", "Promise", "OffSeason"] else 0)
                
                st.markdown("---")
                st.markdown("#### 👥 Gestión de Asistencias (Faltas)")
                st.info("💡 Los deportistas marcados constan como asistentes. Para registrar una falta, simplemente **desmarca** al jugador de esta lista.")
                
                jugadores_prog = [j['nombre'] for j in jugadores if j.get("programa") == e_prog]
                asistentes_previos = sesion_actual.get('asistentes', [])
                
                e_asistentes = st.multiselect(
                    "Deportistas asistentes reales:",
                    options=jugadores_prog,
                    default=[a for a in asistentes_previos if a in jugadores_prog]
                )
                
                if st.form_submit_button("🔄 Actualizar Sesión", use_container_width=True):
                    try:
                        datos_actualizados = {
                            "fecha": str(e_fecha),
                            "hora_inicio": str(e_hora),
                            "tipo": e_tipo,
                            "programa": e_prog,
                            "asistentes": e_asistentes,
                            "comentarios": ""
                        }
                        supabase.table("sesiones_entrenamiento").update(datos_actualizados).eq("id", sesion_editar_id).execute()
                        cargar_datos_sistema(force_refresh=True)
                        st.success("¡Sesión actualizada correctamente!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al actualizar la sesión: {e}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Eliminar Sesión Definitivamente", type="primary", use_container_width=True):
                try:
                    supabase.table("sesiones_entrenamiento").delete().eq("id", sesion_editar_id).execute()
                    cargar_datos_sistema(force_refresh=True)
                    st.success("¡Sesión eliminada!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
