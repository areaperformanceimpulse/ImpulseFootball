import streamlit as st
from database.db_manager import supabase, cargar_datos_sistema
from utils.math_helpers import aplicar_estilos_base
from datetime import date
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Valoraciones - ImpulseFootball", page_icon="📊", layout="wide")
aplicar_estilos_base()

if not st.session_state.get("autenticado", False):
    st.warning("Sesión caducada.")
    st.stop()

# Asegurar datos frescos
cargar_datos_sistema()

st.title("📊 Valoraciones Condicionales (Gimnasio)")

tab_reg, tab_nuevo, tab_progreso = st.tabs(["📋 Historial de Registros", "➕ Añadir Nueva Valoración", "📈 Perfil y Progreso Individual"])

jugadores = st.session_state.get("jugadores", [])
valoraciones = st.session_state.get("valoraciones", [])
mapa_jugadores = {j['id']: j['nombre'] for j in jugadores}

with tab_reg:
    st.markdown("### 📋 Listado General de Valoraciones")
    if not valoraciones:
        st.info("No hay valoraciones registradas todavía.")
    else:
        df_vals = pd.DataFrame(valoraciones)
        df_vals['Deportista'] = df_vals['jugador_id'].map(mapa_jugadores)
        
        columnas_ver = ['fecha', 'temporada', 'numero_valoracion', 'Deportista', 'lesion', 'rm_sentadilla_est', 'rm_peso_muerto_est', 'comentarios']
        cols_existentes = [c for c in columnas_ver if c in df_vals.columns]
        st.dataframe(df_vals[cols_existentes], use_container_width=True, hide_index=True)

with tab_nuevo:
    st.markdown("### 📝 Registrar Nueva Valoración")
    if not jugadores:
        st.warning("Primero debes registrar deportistas en la sección de Jugadores.")
    else:
        with st.form("form_nueva_val_optimizado"):
            
            # --- DATOS GENERALES ---
            st.markdown("#### ⚙️ Datos Generales")
            c_g1, c_g2, c_g3, c_g4 = st.columns(4)
            
            with c_g1:
                jugador_sel = st.selectbox("Deportista:", options=list(mapa_jugadores.keys()), format_func=lambda x: mapa_jugadores[x])
            with c_g2:
                # Selector automático de temporada (ej. 25/26)
                anos_disponibles = [f"{str(y)[-2:]}/{str(y+1)[-2:]}" for y in range(2024, 2030)]
                temporada = st.selectbox("Temporada:", options=anos_disponibles, index=1)
            with c_g3:
                num_val = st.number_input("Nº de Valoración:", min_value=1, max_value=10, value=1, step=1)
            with c_g4:
                lesion = st.radio("¿Lesión activa?", options=["No", "Sí"], horizontal=True, index=0)
            
            fecha_test = st.date_input("Fecha del Test:", value=date.today())
            
            st.markdown("---")
            
            # --- MOVILIDAD (FMS) UNILATERAL ---
            st.markdown("#### 🤸 Movilidad: Protocolo FMS (Evaluación Bilateral: 0 a 3)")
            st.markdown("<small style='color: #64748b;'>Selecciona de forma rápida la puntuación para cada lado.</small>", unsafe_allow_html=True)
            
            def selector_fms_lateral(nombre_prueba):
                st.markdown(f"**{nombre_prueba}**")
                col_d, col_i = st.columns(2)
                with col_d:
                    val_d = st.radio(f"Der - {nombre_prueba}", options=[0, 1, 2, 3], horizontal=True, key=f"fms_{nombre_prueba}_d", index=3)
                with col_i:
                    val_i = st.radio(f"Izq - {nombre_prueba}", options=[0, 1, 2, 3], horizontal=True, key=f"fms_{nombre_prueba}_i", index=3)
                return val_d, val_i

            col_f1, col_f2 = st.columns(2)
            with col_f1:
                fms_obs_d, fms_obs_i = selector_fms_lateral("Paso de Obstáculo")
                fms_zan_d, fms_zan_i = selector_fms_lateral("Zancada en Línea")
            with col_f2:
                fms_hom_d, fms_hom_i = selector_fms_lateral("Movilidad de Hombro")
                fms_elev_d, fms_elev_i = selector_fms_lateral("Elevación Pierna Recta")

            st.markdown("---")
            
            # --- 1RM Y VELOCIDAD (ENCODER) ---
            st.markdown("#### 🏋️‍♂️ Estimación 1RM (Fuerza / Velocidad)")
            st.markdown("<small style='color: #64748b;'>Introduce los kg y la velocidad medida con el encoder para calcular la estimación.</small>", unsafe_allow_html=True)
            
            col_r1, col_r2 = st.columns(2)
            
            with col_r1:
                st.markdown("**Sentadilla**")
                kg_sq = st.number_input("Kg Levantados (Sentadilla)", min_value=0.0, value=0.0, step=2.5, key="kg_sq")
                vel_sq = st.number_input("Velocidad (m/s)", min_value=0.0, value=0.0, step=0.05, key="vel_sq")
                # Cálculo automático orientativo de estimación 1RM si hay velocidad y kg (Ejemplo simple de estimación o lectura directa)
                rm_sq_est = kg_sq / (vel_sq / 1.0) if vel_sq > 0 else kg_sq
                st.info(f"💡 **1RM Estimado Sentadilla:** {round(rm_sq_est, 1)} kg")

            with col_r2:
                st.markdown("**Peso Muerto**")
                kg_pm = st.number_input("Kg Levantados (Peso Muerto)", min_value=0.0, value=0.0, step=2.5, key="kg_pm")
                vel_pm = st.number_input("Velocidad (m/s)", min_value=0.0, value=0.0, step=0.05, key="vel_pm")
                rm_pm_est = kg_pm / (vel_pm / 1.0) if vel_pm > 0 else kg_pm
                st.info(f"💡 **1RM Estimado Peso Muerto:** {round(rm_pm_est, 1)} kg")

            st.markdown("---")
            comentarios = st.text_area("Observaciones Generales de la Valoración:")
            
            if st.form_submit_button("💾 Guardar Valoración Completa", use_container_width=True):
                try:
                    nuevo_test = {
                        "jugador_id": jugador_sel,
                        "fecha": str(fecha_test),
                        "temporada": temporada,
                        "numero_valoracion": int(num_val),
                        "lesion": lesion,
                        # FMS Der/Izq
                        "fms_obs_der": fms_obs_d, "fms_obs_izq": fms_obs_i,
                        "fms_zan_der": fms_zan_d, "fms_zan_izq": fms_zan_i,
                        "fms_hom_der": fms_hom_d, "fms_hom_izq": fms_hom_i,
                        "fms_elev_der": fms_elev_d, "fms_elev_izq": fms_elev_i,
                        # Encoder y 1RM
                        "kg_sentadilla": kg_sq, "vel_sentadilla": vel_sq, "rm_sentadilla_est": round(rm_sq_est, 1),
                        "kg_peso_muerto": kg_pm, "vel_peso_muerto": vel_pm, "rm_peso_muerto_est": round(rm_pm_est, 1),
                        "comentarios": comentarios
                    }
                    supabase.table("valoraciones_condicionales").insert(nuevo_test).execute()
                    cargar_datos_sistema()
                    st.success("¡Valoración guardada correctamente en Supabase!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar en Supabase (asegúrate de que las columnas nuevas existan en la tabla): {e}")

with tab_progreso:
    st.markdown("### 📈 Evolución y Perfil Individual")
    if not jugadores:
        st.info("Registra deportistas para ver su progreso.")
    else:
        jug_sel_prog = st.selectbox("Seleccionar deportista para análisis:", options=list(mapa_jugadores.keys()), format_func=lambda x: mapa_jugadores[x], key="select_prog")
        vals_jugador = [v for v in valoraciones if v.get('jugador_id') == jug_sel_prog]
        
        if not vals_jugador:
            st.warning("Este deportista todavía no tiene valoraciones registradas.")
        else:
            df_pj = pd.DataFrame(vals_jugador).sort_values('fecha')
            st.markdown(f"**Evolución histórica de {mapa_jugadores[jug_sel_prog]}**")
            
            if 'rm_sentadilla_est' in df_pj.columns:
                fig_rm = px.line(df_pj, x='fecha', y=['rm_sentadilla_est', 'rm_peso_muerto_est'], markers=True, title="Evolución 1RM Estimado (kg)")
                st.plotly_chart(fig_rm, use_container_width=True)
