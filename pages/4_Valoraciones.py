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
    st.markdown("### 📝 Registrar Nueva Valoración")
    if not jugadores:
        st.warning("Primero debes registrar deportistas en la sección de Jugadores.")
    else:
        with st.form("form_nueva_val_completa"):
            
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
            
            # --- MOVILIDAD (FMS) UNILATERAL ESPECÍFICA ---
            st.markdown("#### 🤸 1️⃣ Movilidad: Protocolo FMS (Evaluación Bilateral: 0 a 3)")
            
            def selector_fms_lateral(nombre_prueba, key_sufix):
                st.markdown(f"**{nombre_prueba}**")
                col_d, col_i = st.columns(2)
                with col_d:
                    val_d = st.selectbox(f"Der - {nombre_prueba}", options=[0, 1, 2, 3], index=3, key=f"fms_{key_sufix}_d")
                with col_i:
                    val_i = st.selectbox(f"Izq - {nombre_prueba}", options=[0, 1, 2, 3], index=3, key=f"fms_{key_sufix}_i")
                return val_d, val_i

            col_f1, col_f2 = st.columns(2)
            with col_f1:
                fms_obs_d, fms_obs_i = selector_fms_lateral("Paso de Obstáculos", "obs")
                fms_zan_d, fms_zan_i = selector_fms_lateral("Zancada en Línea", "zan")
            with col_f2:
                fms_hom_d, fms_hom_i = selector_fms_lateral("Movilidad de Hombro", "hom")
                fms_elev_d, fms_elev_i = selector_fms_lateral("Elevación Pierna Recta", "elev")

            st.markdown("---")
            
            # --- TEST DE SALTO (CMJ Y HORIZONTAL) ---
            st.markdown("#### 🦘 2️⃣ Test de Salto (cm)")
            s1, s2, s3, s4, s5 = st.columns(5)
            cmj_bi = s1.number_input("CMJ Bilateral", value=0.0)
            cmj_ud = s2.number_input("CMJ Uni Der", value=0.0)
            cmj_ui = s3.number_input("CMJ Uni Izq", value=0.0)
            sh_d = s4.number_input("Salto Horiz. Der", value=0.0)
            sh_i = s5.number_input("Salto Horiz. Izq", value=0.0)
            
            st.markdown("---")
            
            # --- FUERZA MÁXIMA ISOMÉTRICA ---
            st.markdown("#### ⚡ 3️⃣ Fuerza Máxima Isométrica (N)")
            i1, i2, i3, i4 = st.columns(4)
            iso_ext_d = i1.number_input("Ext. Rodilla Der", value=0.0)
            iso_ext_i = i2.number_input("Ext. Rodilla Izq", value=0.0)
            iso_flx_d = i3.number_input("Flex. Rodilla Der", value=0.0)
            iso_flx_i = i4.number_input("Flex. Rodilla Izq", value=0.0)
            
            i5, i6, i7, i8 = st.columns(4)
            iso_add_d = i5.number_input("Add Cadera Der", value=0.0)
            iso_add_i = i6.number_input("Add Cadera Izq", value=0.0)
            iso_abd_d = i7.number_input("Abd Cadera Der", value=0.0)
            iso_abd_i = i8.number_input("Abd Cadera Izq", value=0.0)
            
            st.markdown("---")
            
            # --- ESTIMACIÓN 1RM CON ENCODER (KGS + VELOCIDAD) ---
            st.markdown("#### 🏋️‍♂️ 4️⃣ Estimación 1RM (Encoder - kg y Velocidad)")
            r1, r2 = st.columns(2)
            
            with r1:
                st.markdown("**Sentadilla**")
                kg_sq = st.number_input("Kg Sentadilla", min_value=0.0, value=0.0, step=2.5, key="kg_sq")
                vel_sq = st.number_input("Velocidad Sentadilla (m/s)", min_value=0.0, value=0.0, step=0.05, key="vel_sq")
                # Cálculo automático de estimación 1RM en función de velocidad y kg
                rm_sq = kg_sq / (vel_sq / 1.0) if vel_sq > 0 else kg_sq
                st.info(f"💡 **1RM Estimado Sentadilla:** {round(rm_sq, 1)} kg")

            with r2:
                st.markdown("**Peso Muerto**")
                kg_pm = st.number_input("Kg Peso Muerto", min_value=0.0, value=0.0, step=2.5, key="kg_pm")
                vel_pm = st.number_input("Velocidad Peso Muerto (m/s)", min_value=0.0, value=0.0, step=0.05, key="vel_pm")
                rm_pm = kg_pm / (vel_pm / 1.0) if vel_pm > 0 else kg_pm
                st.info(f"💡 **1RM Estimado Peso Muerto:** {round(rm_pm, 1)} kg")

            st.markdown("---")
            comentarios = st.text_area("Observaciones del Evaluador:")
            
            if st.form_submit_button("💾 Guardar Valoración Completa", use_container_width=True):
                try:
                    nuevo_test = {
                        "jugador_id": jugador_sel,
                        "fecha": str(fecha_test),
                        "temporada": temporada,
                        "numero_valoracion": int(num_val),
                        "lesion": lesion,
                        # FMS Unilateral
                        "fms_paso_obstaculo_der": fms_obs_d, "fms_paso_obstaculo_izq": fms_obs_i,
                        "fms_zancada_der": fms_zan_d, "fms_zancada_izq": fms_zan_i,
                        "fms_mov_hombro_der": fms_hom_d, "fms_mov_hombro_izq": fms_hom_i,
                        "fms_elevacion_pierna_der": fms_elev_d, "fms_elevacion_pierna_izq": fms_elev_i,
                        # Saltos
                        "cmj_bilateral": cmj_bi, "cmj_uni_der": cmj_ud, "cmj_uni_izq": cmj_ui,
                        "salto_horiz_der": sh_d, "salto_horiz_izq": sh_i,
                        # Isometría
                        "iso_ext_rodilla_der": iso_ext_d, "iso_ext_rodilla_izq": iso_ext_i,
                        "iso_flex_rodilla_der": iso_flx_d, "iso_flex_rodilla_izq": iso_flx_i,
                        "iso_add_cadera_der": iso_add_d, "iso_add_cadera_izq": iso_add_i,
                        "iso_abd_cadera_der": iso_abd_d, "iso_abd_cadera_izq": iso_abd_i,
                        # 1RM (con valores calculados)
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
            
            # Gráfica de 1RM
            if 'rm_sentadilla' in df_pj.columns:
                fig_rm = px.line(df_pj, x='fecha', y=['rm_sentadilla', 'rm_peso_muerto'], markers=True, title="Evolución Estimación 1RM (kg)")
                st.plotly_chart(fig_rm, use_container_width=True)
                
            # Gráfica de Saltos
            if 'cmj_bilateral' in df_pj.columns:
                fig_cmj = px.line(df_pj, x='fecha', y=['cmj_bilateral', 'cmj_uni_der', 'cmj_uni_izq'], markers=True, title="Evolución Altura de Salto - CMJ (cm)")
                st.plotly_chart(fig_cmj, use_container_width=True)
