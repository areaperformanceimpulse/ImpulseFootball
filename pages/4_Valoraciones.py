import streamlit as st
from database.db_manager import supabase, cargar_datos_sistema
from utils.math_helpers import aplicar_estilos_base, calcular_asimetria, safe_float
from datetime import date
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Valoraciones - ImpulseFootball", page_icon="📊", layout="wide")
aplicar_estilos_base()

if not st.session_state.get("autenticado", False):
    st.warning("Sesión caducada.")
    st.stop()

st.title("📊 Valoraciones Condicionales (Gimnasio)")

tab_reg, tab_nuevo, tab_progreso = st.tabs(["📋 Historial de Registros", "➕ Añadir Nueva Valoración", "📈 Perfil y Progreso Individual"])

jugadores = st.session_state.get("jugadores", [])
valoraciones = st.session_state.get("valoraciones", [])

# Diccionario para traducir IDs de jugadores a nombres
mapa_jugadores = {j['id']: j['nombre'] for j in jugadores}

with tab_reg:
    st.markdown("### 📋 Listado General de Valoraciones")
    if not valoraciones:
        st.info("No hay valoraciones registradas todavía.")
    else:
        df_vals = pd.DataFrame(valoraciones)
        df_vals['Deportista'] = df_vals['jugador_id'].map(mapa_jugadores)
        
        # Mostrar tabla resumida
        columnas_ver = ['fecha', 'Deportista', 'cmj_bilateral', 'rm_sentadilla', 'rm_peso_muerto', 'comentarios']
        cols_existentes = [c for c in columnas_ver if c in df_vals.columns]
        st.dataframe(df_vals[cols_existentes], use_container_width=True, hide_index=True)

with tab_nuevo:
    st.markdown("### 📝 Registrar Nueva Batería de Test (3 al año)")
    if not jugadores:
        st.warning("Primero debes registrar deportistas en la sección de Jugadores.")
    else:
        with st.form("form_nueva_val"):
            jugador_sel = st.selectbox("Seleccionar Deportista:", options=list(mapa_jugadores.keys()), format_func=lambda x: mapa_jugadores[x])
            fecha_test = st.date_input("Fecha de la Valoración:", value=date.today())
            
            st.markdown("---")
            st.markdown("#### 1️⃣ Movilidad: Protocolo FMS (0 a 3)")
            c1, c2, c3, c4 = st.columns(4)
            fms_1 = c1.slider("Sentadilla profunda", 0, 3, 3)
            fms_2 = c2.slider("Paso de obstáculos", 0, 3, 3)
            fms_3 = c3.slider("Zancada en línea", 0, 3, 3)
            fms_4 = c4.slider("Movilidad de hombro", 0, 3, 3)
            c5, c6, c7 = st.columns(3)
            fms_5 = c5.slider("Elevación pierna recta", 0, 3, 3)
            fms_6 = c6.slider("Estabilidad de tronco", 0, 3, 3)
            fms_7 = c7.slider("Estabilidad rotatoria", 0, 3, 3)
            
            st.markdown("---")
            st.markdown("#### 2️⃣ Test de Salto (cm)")
            s1, s2, s3, s4, s5 = st.columns(5)
            cmj_bi = s1.number_input("CMJ Bilateral", value=0.0)
            cmj_ud = s2.number_input("CMJ Uni Der", value=0.0)
            cmj_ui = s3.number_input("CMJ Uni Izq", value=0.0)
            sh_d = s4.number_input("Salto Horiz. Der", value=0.0)
            sh_i = s5.number_input("Salto Horiz. Izq", value=0.0)
            
            st.markdown("---")
            st.markdown("#### 3️⃣ Fuerza Máxima Isométrica (N)")
            i1, i2, i3, i4 = st.columns(4)
            iso_ext_d = i1.number_input("Ext. Rodilla Der", value=0.0)
            iso_ext_i = i1.number_input("Ext. Rodilla Izq", value=0.0)
            iso_flx_d = i2.number_input("Flex. Rodilla Der", value=0.0)
            iso_flx_i = i2.number_input("Flex. Rodilla Izq", value=0.0)
            iso_add_d = i3.number_input("Add Cadera Der", value=0.0)
            iso_add_i = i3.number_input("Add Cadera Izq", value=0.0)
            iso_abd_d = i4.number_input("Abd Cadera Der", value=0.0)
            iso_abd_i = i4.number_input("Abd Cadera Izq", value=0.0)
            
            st.markdown("---")
            st.markdown("#### 4️⃣ Estimación 1RM (Encoder - kg)")
            r1, r2 = st.columns(2)
            rm_sq = r1.number_input("1RM Sentadilla (kg)", value=0.0)
            rm_pm = r2.number_input("1RM Peso Muerto (kg)", value=0.0)
            
            comentarios = st.text_area("Observaciones del Evaluador:")
            
            if st.form_submit_button("💾 Guardar Valoración Completa", use_container_width=True):
                try:
                    nuevo_test = {
                        "jugador_id": jugador_sel,
                        "fecha": str(fecha_test),
                        "fms_sentadilla": fms_1, "fms_paso_obstaculo": fms_2, "fms_zancada": fms_3,
                        "fms_mov_hombro": fms_4, "fms_elevacion_pierna": fms_5, "fms_estabilidad_tronco": fms_6,
                        "fms_estabilidad_rotatoria": fms_7,
                        "cmj_bilateral": cmj_bi, "cmj_uni_der": cmj_ud, "cmj_uni_izq": cmj_ui,
                        "salto_horiz_der": sh_d, "salto_horiz_izq": sh_i,
                        "iso_ext_rodilla_der": iso_ext_d, "iso_ext_rodilla_izq": iso_ext_i,
                        "iso_flex_rodilla_der": iso_flx_d, "iso_flex_rodilla_izq": iso_flx_i,
                        "iso_add_cadera_der": iso_add_d, "iso_add_cadera_izq": iso_add_i,
                        "iso_abd_cadera_der": iso_abd_d, "iso_abd_cadera_izq": iso_abd_i,
                        "rm_sentadilla": rm_sq, "rm_peso_muerto": rm_pm,
                        "comentarios": comentarios
                    }
                    supabase.table("valoraciones_condicionales").insert(nuevo_test).execute()
                    cargar_datos_sistema()
                    st.success("¡Valoración guardada correctamente en Supabase!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

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
            
            # Gráfica de 1RM
            if 'rm_sentadilla' in df_pj.columns:
                fig_rm = px.line(df_pj, x='fecha', y=['rm_sentadilla', 'rm_peso_muerto'], markers=True, title="Evolución Estimación 1RM (kg)")
                st.plotly_chart(fig_rm, use_container_width=True)
                
            # Gráfica de Saltos
            if 'cmj_bilateral' in df_pj.columns:
                fig_cmj = px.line(df_pj, x='fecha', y=['cmj_bilateral', 'cmj_uni_der', 'cmj_uni_izq'], markers=True, title="Evolución Altura de Salto - CMJ (cm)")
                st.plotly_chart(fig_cmj, use_container_width=True)
