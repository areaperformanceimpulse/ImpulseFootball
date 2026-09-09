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
        
        columnas_ver = ['fecha', 'temporada', 'numero_valoracion', 'Deportista', 'lesion', 'cmj_bilateral', 'rm_sentadilla', 'rm_peso_muerto', 'comentarios']
        cols_existentes = [c for c in columnas_ver if c in df_vals.columns]
        st.dataframe(df_vals[cols_existentes], use_container_width=True, hide_index=True)

with tab_nuevo:
    st.markdown("### 📝 Registrar Nueva Valoración Completa")
    if not jugadores:
        st.warning("Primero debes registrar deportistas en la sección de Jugadores.")
    else:
        with st.form("form_nueva_val_detallada"):
            
            # --- DATOS GENERALES ---
            st.markdown("#### ⚙️ Datos Generales")
            c_g1, c_g2, c_g3, c_g4 = st.columns(4)
            
            with c_g1:
                jugador_sel = st.selectbox("Deportista:", options=list(mapa_jugadores.keys()), format_func=lambda x: mapa_jugadores[x])
            with c_g2:
                anos_disponibles = [f"{str(y)[-2:]}/{str(y+1)[-2:]}" for y in range(2024, 2030)]
                temporada = st.selectbox("Temporada:", options=anos_disponibles, index=1)
            with c_g3:
                num_val = st.number_input("Nº de Valoración:", min_value=1, max_value=10, value=1, step=1)
            with c_g4:
                lesion = st.radio("¿Lesión activa?", options=["No", "Sí"], horizontal=True, index=0)
            
            fecha_test = st.date_input("Fecha del Test:", value=date.today())
            
            st.markdown("---")
            
            # ==========================================
            # 1. MOVILIDAD (FMS): 7 PRUEBAS (CON BOTONES NUMÉRICOS + Y -)
            # ==========================================
            st.markdown("#### 🤸 1. Protocolo FMS (Movilidad y Estabilidad - Puntuación 0 a 3)")
            
            def tarjeta_fms_numerica(titulo, es_unilateral=True):
                st.markdown(f"**{titulo}**")
                if es_unilateral:
                    cd, ci = st.columns(2)
                    with cd:
                        val_d = st.number_input(f"{titulo} (Derecha)", min_value=0, max_value=3, value=3, step=1, key=f"fms_{titulo}_der")
                    with ci:
                        val_i = st.number_input(f"{titulo} (Izquierda)", min_value=0, max_value=3, value=3, step=1, key=f"fms_{titulo}_izq")
                    return val_d, val_i
                else:
                    val = st.number_input(f"{titulo} (Bilateral)", min_value=0, max_value=3, value=3, step=1, key=f"fms_{titulo}_bi")
                    return val

            c_f1, c_f2 = st.columns(2)
            with c_f1:
                fms_sentadilla = tarjeta_fms_numerica("Sentadilla Profunda", es_unilateral=False)
                fms_obstaculo_d, fms_obstaculo_i = tarjeta_fms_numerica("Paso de Obstáculos", es_unilateral=True)
                fms_zancada_d, fms_zancada_i = tarjeta_fms_numerica("Zancada en Línea", es_unilateral=True)
                fms_hombro_d, fms_hombro_i = tarjeta_fms_numerica("Movilidad de Hombro", es_unilateral=True)
            with c_f2:
                fms_pierna_d, fms_pierna_i = tarjeta_fms_numerica("Elevación de Pierna Recta", es_unilateral=True)
                fms_tronco = tarjeta_fms_numerica("Estabilidad de Tronco en Flexión", es_unilateral=False)
                fms_rotatoria = tarjeta_fms_numerica("Estabilidad Rotatoria", es_unilateral=False)

            st.markdown("---")
            
            # ==========================================
            # 2. TEST DE SALTO (3 TARJETAS INDEPENDIENTES)
            # ==========================================
            st.markdown("#### 🦘 2. Test de Salto")
            
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.markdown("**CMJ Bilateral (cm)**")
                cmj_bi = st.number_input("Altura CMJ Bilateral", min_value=0.0, value=0.0, step=0.5, label_visibility="collapsed")
            with col_s2:
                st.markdown("**CMJ Unilateral (cm)**")
                cmj_ud = st.number_input("CMJ Unilateral Derecha", min_value=0.0, value=0.0, step=0.5)
                cmj_ui = st.number_input("CMJ Unilateral Izquierda", min_value=0.0, value=0.0, step=0.5)
            with col_s3:
                st.markdown("**Salto Horizontal (cm)**")
                sh_d = st.number_input("Salto Horizontal Derecha", min_value=0.0, value=0.0, step=1.0)
                sh_i = st.number_input("Salto Horizontal Izquierda", min_value=0.0, value=0.0, step=1.0)

            st.markdown("---")
            
            # ==========================================
            # 3. FUERZA MÁXIMA ISOMÉTRICA (TARJETAS POR MOVIMIENTO)
            # ==========================================
            st.markdown("#### ⚡ 3. Fuerza Máxima Isométrica (N)")
            
            ci1, ci2 = st.columns(2)
            with ci1:
                st.markdown("**Extensión de Rodilla (N)**")
                iso_ext_d = st.number_input("Extensión de Rodilla Derecha", min_value=0.0, value=0.0, step=1.0)
                iso_ext_i = st.number_input("Extensión de Rodilla Izquierda", min_value=0.0, value=0.0, step=1.0)
                
                st.markdown("**Aductores de Cadera (N)**")
                iso_add_d = st.number_input("Aductores Derecha", min_value=0.0, value=0.0, step=1.0)
                iso_add_i = st.number_input("Aductores Izquierda", min_value=0.0, value=0.0, step=1.0)
            with ci2:
                st.markdown("**Flexión de Rodilla (N)**")
                iso_flx_d = st.number_input("Flexión de Rodilla Derecha", min_value=0.0, value=0.0, step=1.0)
                iso_flx_i = st.number_input("Flexión de Rodilla Izquierda", min_value=0.0, value=0.0, step=1.0)
                
                st.markdown("**Abductores de Cadera (N)**")
                iso_abd_d = st.number_input("Abductores Derecha", min_value=0.0, value=0.0, step=1.0)
                iso_abd_i = st.number_input("Abductores Izquierda", min_value=0.0, value=0.0, step=1.0)

            st.markdown("---")
            
            # ==========================================
            # 4. ESTIMACIÓN 1RM (5 SERIES: PESO Y VELOCIDAD)
            # ==========================================
            st.markdown("#### 🏋️‍♂️ 4. Estimación 1RM (5 Series de Carga y Velocidad)")
            st.markdown("<small style='color: #64748b;'>Introduce los kg y la velocidad medida del encoder para cada una de las 5 series progresivas.</small>", unsafe_allow_html=True)
            
            def capturar_5_series_dinamico(nombre_ejercicio, key_prefix):
                st.markdown(f"**{nombre_ejercicio}**")
                pesos_series = []
                vels_series = []
                
                for s in range(1, 6):
                    cs1, cs2 = st.columns(2)
                    with cs1:
                        p = st.number_input(f"Serie {s} - Kg ({nombre_ejercicio})", min_value=0.0, value=0.0, step=2.5, key=f"{key_prefix}_p_{s}")
                    with cs2:
                        v = st.number_input(f"Serie {s} - Velocidad m/s ({nombre_ejercicio})", min_value=0.0, value=0.0, step=0.01, key=f"{key_prefix}_v_{s}")
                    pesos_series.append(p)
                    vels_series.append(v)
                
                # Cálculo directo en tiempo real basado en los inputs actuales
                validas = [(pesos_series[i], vels_series[i]) for i in range(5) if vels_series[i] > 0 and pesos_series[i] > 0]
                if validas:
                    p_max, v_max = max(validas, key=lambda x: x[0])
                    rm_est = p_max / (v_max / 1.0) if v_max > 0 else p_max
                else:
                    rm_est = max(pesos_series) if max(pesos_series) > 0 else 0.0
                
                return rm_est, pesos_series, vels_series

            cr1, cr2 = st.columns(2)
            with cr1:
                rm_sq, p_sq_list, v_sq_list = capturar_5_series_dinamico("Sentadilla", "sq")
                st.info(f"💡 **1RM Estimado (Sentadilla):** {round(rm_sq, 1)} kg")
            with cr2:
                rm_pm, p_pm_list, v_pm_list = capturar_5_series_dinamico("Peso Muerto", "pm")
                st.info(f"💡 **1RM Estimado (Peso Muerto):** {round(rm_pm, 1)} kg")

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
                        # 7 Pruebas FMS
                        "fms_sentadilla": fms_sentadilla,
                        "fms_paso_obstaculo_der": fms_obstaculo_d, "fms_paso_obstaculo_izq": fms_obstaculo_i,
                        "fms_zancada_der": fms_zancada_d, "fms_zancada_izq": fms_zancada_i,
                        "fms_mov_hombro_der": fms_hombro_d, "fms_mov_hombro_izq": fms_hombro_i,
                        "fms_elevacion_pierna_der": fms_pierna_d, "fms_elevacion_pierna_izq": fms_pierna_i,
                        "fms_estabilidad_tronco": fms_tronco,
                        "fms_estabilidad_rotatoria": fms_rotatoria,
                        # Saltos
                        "cmj_bilateral": cmj_bi, "cmj_uni_der": cmj_ud, "cmj_uni_izq": cmj_ui,
                        "salto_horiz_der": sh_d, "salto_horiz_izq": sh_i,
                        # Isometría
                        "iso_ext_rodilla_der": iso_ext_d, "iso_ext_rodilla_izq": iso_ext_i,
                        "iso_flex_rodilla_der": iso_flx_d, "iso_flex_rodilla_izq": iso_flx_i,
                        "iso_add_cadera_der": iso_add_d, "iso_add_cadera_izq": iso_add_i,
                        "iso_abd_cadera_der": iso_abd_d, "iso_abd_cadera_izq": iso_abd_i,
                        # 1RM Estimado final
                        "rm_sentadilla": round(rm_sq, 1),
                        "rm_peso_muerto": round(rm_pm, 1),
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
            
            if 'rm_sentadilla' in df_pj.columns:
                fig_rm = px.line(df_pj, x='fecha', y=['rm_sentadilla', 'rm_peso_muerto'], markers=True, title="Evolución Estimación 1RM (kg)")
                st.plotly_chart(fig_rm, use_container_width=True)
                
            if 'cmj_bilateral' in df_pj.columns:
                fig_cmj = px.line(df_pj, x='fecha', y=['cmj_bilateral', 'cmj_uni_der', 'cmj_uni_izq'], markers=True, title="Evolución Altura de Salto - CMJ (cm)")
                st.plotly_chart(fig_cmj, use_container_width=True)
