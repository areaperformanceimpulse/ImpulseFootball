import streamlit as st
from database.db_manager import supabase, cargar_datos_sistema
from utils.math_helpers import aplicar_estilos_base, calcular_asimetria
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

tab_nuevo, tab_informes, tab_reg = st.tabs(["➕ Añadir Nueva Valoración", "📈 Informes de valoraciones", "📋 Tabla de registros"])

jugadores = st.session_state.get("jugadores", [])
valoraciones = st.session_state.get("valoraciones", [])
mapa_jugadores = {j['id']: j['nombre'] for j in jugadores}

# ==========================================
# PESTAÑA 1: AÑADIR NUEVA VALORACIÓN (COMPRIMIDA)
# ==========================================
with tab_nuevo:
    if not jugadores:
        st.warning("Primero debes registrar deportistas en la sección de Jugadores.")
    else:
        with st.form("form_nueva_val_detallada"):
            
            # --- ⚙️ DATOS GENERALES (5 Variables en 1 fila) ---
            st.markdown("#### ⚙️ Datos Generales")
            cg1, cg2, cg3, cg4, cg5 = st.columns(5)
            with cg1: jugador_sel = st.selectbox("Deportista:", options=list(mapa_jugadores.keys()), format_func=lambda x: mapa_jugadores[x])
            with cg2: 
                anos = [f"{str(y)[-2:]}/{str(y+1)[-2:]}" for y in range(2024, 2030)]
                temporada = st.selectbox("Temporada:", options=anos, index=1)
            with cg3: num_val = st.number_input("N.º de Valoración:", min_value=1, max_value=10, value=1, step=1)
            with cg4: lesion = st.radio("¿Lesión activa?", options=["No", "Sí"], horizontal=True, index=0)
            with cg5: fecha_test = st.date_input("Fecha:", value=date.today())
            
            st.markdown("---")
            
            # --- 🤸 1. FMS (Fila 1: 5 variables | Fila 2: 6 variables) ---
            st.markdown("#### 🤸 1. Protocolo FMS (0 a 3)")
            cf1, cf2, cf3, cf4, cf5 = st.columns(5)
            with cf1: fms_sentadilla = st.number_input("FMS1: Sentadilla profunda", 0, 3, 3)
            with cf2: fms_obstaculo_d = st.number_input("FMS2: Paso de Obstáculo (D).", 0, 3, 3)
            with cf3: fms_obstaculo_i = st.number_input("FMS2: Paso de Obstáculo (I).", 0, 3, 3)
            with cf4: fms_zancada_d = st.number_input("FMS3: Zancada (D).", 0, 3, 3)
            with cf5: fms_zancada_i = st.number_input("FMS3: Zancada (I).", 0, 3, 3)
            
            cf6, cf7, cf8, cf9, cf10, cf11 = st.columns(6)
            with cf6: fms_hombro_d = st.number_input("FMS4: Movilidad de Hombro (D).", 0, 3, 3)
            with cf7: fms_hombro_i = st.number_input("FMS4: Movilidad de Hombro (I)", 0, 3, 3)
            with cf8: fms_pierna_d = st.number_input("FMS5: Elevación de pierna (D)", 0, 3, 3)
            with cf9: fms_pierna_i = st.number_input("FMS5: Elevación de pierna (I)", 0, 3, 3)
            with cf10: fms_tronco = st.number_input("FMS6: Estabilidad de Tronco", 0, 3, 3)
            with cf11: fms_rotatoria = st.number_input("FMS7: Estabilidad Rotatoria", 0, 3, 3)

            st.markdown("---")
            
            # --- 🦘 2. SALTO (5 Variables en 1 fila) ---
            st.markdown("#### 🦘 2. Test de Salto (cm)")
            cs1, cs2, cs3, cs4, cs5 = st.columns(5)
            with cs1: cmj_bi = st.number_input("CMJ Bilateral", min_value=0.0, value=0.0, step=0.5)
            with cs2: cmj_ud = st.number_input("CMJ Unilateral (D)", min_value=0.0, value=0.0, step=0.5)
            with cs3: cmj_ui = st.number_input("CMJ Unilateral (I)", min_value=0.0, value=0.0, step=0.5)
            with cs4: sh_d = st.number_input("Salto horizontal (D).", min_value=0.0, value=0.0, step=1.0)
            with cs5: sh_i = st.number_input("Salto horizontal (I)", min_value=0.0, value=0.0, step=1.0)

            st.markdown("---")
            
            # --- ⚡ 3. ISOMETRÍA (4 Bloques, Der/Izq en horizontal) ---
            st.markdown("#### ⚡ 3. Fuerza Máxima Isométrica (N)")
            ci1, ci2, ci3, ci4 = st.columns(4)
            with ci1:
                st.markdown("**Extensión de Rodilla**")
                c_ed, c_ei = st.columns(2)
                with c_ed: iso_ext_d = st.number_input("Derecha", min_value=0.0, value=0.0, step=1.0, key="ext_d")
                with c_ei: iso_ext_i = st.number_input("Izquierda", min_value=0.0, value=0.0, step=1.0, key="ext_i")
            with ci2:
                st.markdown("**Flexión de Rodilla**")
                c_fd, c_fi = st.columns(2)
                with c_fd: iso_flx_d = st.number_input("Derecha", min_value=0.0, value=0.0, step=1.0, key="flx_d")
                with c_fi: iso_flx_i = st.number_input("Izquierda", min_value=0.0, value=0.0, step=1.0, key="flx_i")
            with ci3:
                st.markdown("**Aducción de Cadera**")
                c_ad, c_ai = st.columns(2)
                with c_ad: iso_add_d = st.number_input("Derecha", min_value=0.0, value=0.0, step=1.0, key="add_d")
                with c_ai: iso_add_i = st.number_input("Izquierda", min_value=0.0, value=0.0, step=1.0, key="add_i")
            with ci4:
                st.markdown("**Abducción de Cadera**")
                c_abd, c_abi = st.columns(2)
                with c_abd: iso_abd_d = st.number_input("Derecha", min_value=0.0, value=0.0, step=1.0, key="abd_d")
                with c_abi: iso_abd_i = st.number_input("Izquierda", min_value=0.0, value=0.0, step=1.0, key="abd_i")

            st.markdown("---")
            
            # --- 🏋️‍♂️ 4. 1RM (10 Columnas para SQ, 10 Columnas para PM debajo) ---
            st.markdown("#### 🏋️‍♂️ 4. Estimación 1RM (Carga y Velocidad)")
            
            st.markdown("**Sentadilla**")
            c_sq = st.columns(10)
            p_sq, v_sq = [], []
            for s in range(5):
                with c_sq[s*2]: p_sq.append(st.number_input(f"S{s+1}(kg)", min_value=0.0, step=2.5, key=f"sq_p_{s}"))
                with c_sq[s*2+1]: v_sq.append(st.number_input(f"S{s+1}(m/s)", min_value=0.0, step=0.01, key=f"sq_v_{s}"))
                
            st.markdown("**Peso Muerto**")
            c_pm = st.columns(10)
            p_pm, v_pm = [], []
            for s in range(5):
                with c_pm[s*2]: p_pm.append(st.number_input(f"S{s+1}(kg)", min_value=0.0, step=2.5, key=f"pm_p_{s}"))
                with c_pm[s*2+1]: v_pm.append(st.number_input(f"S{s+1}(m/s)", min_value=0.0, step=0.01, key=f"pm_v_{s}"))

            # Cálculo interno
            def calcular_rm_final(pesos, vels):
                validas = [(pesos[i], vels[i]) for i in range(5) if vels[i] > 0 and pesos[i] > 0]
                if validas:
                    p_max, v_max = max(validas, key=lambda x: x[0])
                    return round(p_max / v_max, 1)
                return round(max(pesos), 1) if max(pesos) > 0 else 0.0

            rm_sq = calcular_rm_final(p_sq, v_sq)
            rm_pm = calcular_rm_final(p_pm, v_pm)

            st.markdown("---")
            comentarios = st.text_input("Observaciones Generales de la Valoración:")
            
            if st.form_submit_button("💾 Guardar Valoración Completa", use_container_width=True):
                try:
                    nuevo_test = {
                        "jugador_id": jugador_sel, "fecha": str(fecha_test), "temporada": temporada,
                        "numero_valoracion": int(num_val), "lesion": lesion,
                        "fms_sentadilla": fms_sentadilla,
                        "fms_paso_obstaculo_der": fms_obstaculo_d, "fms_paso_obstaculo_izq": fms_obstaculo_i,
                        "fms_zancada_der": fms_zancada_d, "fms_zancada_izq": fms_zancada_i,
                        "fms_mov_hombro_der": fms_hombro_d, "fms_mov_hombro_izq": fms_hombro_i,
                        "fms_elevacion_pierna_der": fms_pierna_d, "fms_elevacion_pierna_izq": fms_pierna_i,
                        "fms_estabilidad_tronco": fms_tronco, "fms_estabilidad_rotatoria": fms_rotatoria,
                        "cmj_bilateral": cmj_bi, "cmj_uni_der": cmj_ud, "cmj_uni_izq": cmj_ui,
                        "salto_horiz_der": sh_d, "salto_horiz_izq": sh_i,
                        "iso_ext_rodilla_der": iso_ext_d, "iso_ext_rodilla_izq": iso_ext_i,
                        "iso_flex_rodilla_der": iso_flx_d, "iso_flex_rodilla_izq": iso_flx_i,
                        "iso_add_cadera_der": iso_add_d, "iso_add_cadera_izq": iso_add_i,
                        "iso_abd_cadera_der": iso_abd_d, "iso_abd_cadera_izq": iso_abd_i,
                        "rm_sentadilla": float(rm_sq), "rm_peso_muerto": float(rm_pm), "comentarios": comentarios
                    }
                    supabase.table("valoraciones_condicionales").insert(nuevo_test).execute()
                    cargar_datos_sistema()
                    st.success("¡Valoración guardada correctamente!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

# ==========================================
# PESTAÑA 2: INFORMES DE VALORACIONES
# ==========================================
with tab_informes:
    st.markdown("### 📈 Informes de Valoraciones y Perfil Individual")
    if not jugadores or not valoraciones:
        st.info("No hay datos suficientes para mostrar informes.")
    else:
        cf1, cf2, cf3 = st.columns(3)
        with cf1: jug_sel_prog = st.selectbox("Deportista:", options=list(mapa_jugadores.keys()), format_func=lambda x: mapa_jugadores[x])
        
        vals_jugador = [v for v in valoraciones if v.get('jugador_id') == jug_sel_prog]
        
        if not vals_jugador:
            st.warning("Este deportista todavía no tiene valoraciones registradas.")
        else:
            df_pj = pd.DataFrame(vals_jugador)
            temporadas = df_pj['temporada'].dropna().unique().tolist()
            
            with cf2: temp_sel = st.selectbox("Temporada:", options=temporadas)
            df_temp = df_pj[df_pj['temporada'] == temp_sel]
            
            if df_temp.empty:
                st.warning("No hay valoraciones en esta temporada.")
            else:
                dicc_vals = {row['id']: f"{row['numero_valoracion']} ({row['fecha']})" for idx, row in df_temp.iterrows()}
                with cf3: val_sel_id = st.selectbox("Número de Valoración:", options=list(dicc_vals.keys()), format_func=lambda x: dicc_vals[x])
                
                v_data = df_temp[df_temp['id'] == val_sel_id].iloc[0]
                
                # Función para inyectar KPIs comprimidos con letra reducida
                def kpi_compacto(titulo, valor):
                    st.markdown(f"<div style='line-height: 1.2; margin-bottom: 12px;'><span style='font-size: 0.80em; color: #64748b; font-weight: 600;'>{titulo}</span><br><span style='font-size: 1.2em; font-weight: 800;'>{valor}</span></div>", unsafe_allow_html=True)

                # Semáforos
                def badge_asi(val):
                    if val < 10: return f"🟢 {val}% (Óptimo)"
                    elif val <= 15: return f"🟡 {val}% (Precaución)"
                    else: return f"🔴 {val}% (Riesgo)"

                def badge_hq(val): return f"🟢 {val}" if val >= 0.6 else f"🔴 {val} (Déficit)"
                def badge_adab(val): return f"🟢 {val}" if val >= 0.9 else f"🔴 {val} (Déficit)"

                st.markdown("---")
                
                # ---------------------------------------------------------
                # 1. MOVILIDAD Y ESTABILIDAD
                # ---------------------------------------------------------
                st.markdown("#### 🤸 1. Análisis de Movilidad y Estabilidad")
                
                cm1, cm2, cm3, cm4, cm5 = st.columns(5)
                with cm1: kpi_compacto("FMS 1: Sentadilla profunda", v_data.get('fms_sentadilla', 0))
                with cm2: kpi_compacto("FMS 2: Paso Obstáculo (D)", v_data.get('fms_paso_obstaculo_der', 0))
                with cm3: kpi_compacto("FMS 2: Paso Obstáculo (I)", v_data.get('fms_paso_obstaculo_izq', 0))
                with cm4: kpi_compacto("FMS 3: Zancada en línea (D)", v_data.get('fms_zancada_der', 0))
                with cm5: kpi_compacto("FMS 3: Zancada en línea (I)", v_data.get('fms_zancada_izq', 0))
                
                cm6, cm7, cm8, cm9, cm10, cm11 = st.columns(6)
                with cm6: kpi_compacto("FMS 4: Movilidad Hombro (D)", v_data.get('fms_mov_hombro_der', 0))
                with cm7: kpi_compacto("FMS 4: Movilidad Hombro (I)", v_data.get('fms_mov_hombro_izq', 0))
                with cm8: kpi_compacto("FMS 5: Elevación Pierna (D)", v_data.get('fms_elevacion_pierna_der', 0))
                with cm9: kpi_compacto("FMS 5: Elevación Pierna (I)", v_data.get('fms_elevacion_pierna_izq', 0))
                with cm10: kpi_compacto("FMS 6: Estabilidad Tronco", v_data.get('fms_estabilidad_tronco', 0))
                with cm11: kpi_compacto("FMS 7: Estabilidad Rotatoria", v_data.get('fms_estabilidad_rotatoria', 0))

                st.markdown("---")

                # ---------------------------------------------------------
                # 2. RENDIMIENTO EN SALTO
                # ---------------------------------------------------------
                st.markdown("#### 🦘 2. Rendimiento en Salto")
                
                cs1, cs2, cs3, cs4, cs5 = st.columns(5)
                with cs1: kpi_compacto("Salto Vertical Bilateral", f"{v_data.get('cmj_bilateral', 0)} cm")
                with cs2: kpi_compacto("Salto Vertical Unilateral (D)", f"{v_data.get('cmj_uni_der', 0)} cm")
                with cs3: kpi_compacto("Salto Vertical Unilateral (I)", f"{v_data.get('cmj_uni_izq', 0)} cm")
                with cs4: kpi_compacto("Salto Horizontal (D)", f"{v_data.get('salto_horiz_der', 0)} cm")
                with cs5: kpi_compacto("Salto Horizontal (I)", f"{v_data.get('salto_horiz_izq', 0)} cm")
                
                asi_cmj = calcular_asimetria(v_data.get('cmj_uni_der', 0), v_data.get('cmj_uni_izq', 0))
                asi_sh = calcular_asimetria(v_data.get('salto_horiz_der', 0), v_data.get('salto_horiz_izq', 0))
                
                ca1, ca2 = st.columns(2)
                ca1.info(f"**Asimetría Salto Vertical Unilateral:** {badge_asi(asi_cmj)}")
                ca2.info(f"**Asimetría Salto Horizontal:** {badge_asi(asi_sh)}")

                st.markdown("---")

                # ---------------------------------------------------------
                # 3. FUERZA MÁXIMA ISOMÉTRICA
                # ---------------------------------------------------------
                st.markdown("#### ⚡ 3. Fuerza Máxima Isométrica")
                
                ci1, ci2, ci3, ci4, ci5, ci6, ci7, ci8 = st.columns(8)
                with ci1: kpi_compacto("Extensión Cuádriceps (D)", f"{v_data.get('iso_ext_rodilla_der', 0)} N")
                with ci2: kpi_compacto("Extensión Cuádriceps (I)", f"{v_data.get('iso_ext_rodilla_izq', 0)} N")
                with ci3: kpi_compacto("Flexión Isquiosurales (D)", f"{v_data.get('iso_flex_rodilla_der', 0)} N")
                with ci4: kpi_compacto("Flexión Isquiosurales (I)", f"{v_data.get('iso_flex_rodilla_izq', 0)} N")
                with ci5: kpi_compacto("Aducción Cadera (D)", f"{v_data.get('iso_add_cadera_der', 0)} N")
                with ci6: kpi_compacto("Aducción Cadera (I)", f"{v_data.get('iso_add_cadera_izq', 0)} N")
                with ci7: kpi_compacto("Abducción Cadera (D)", f"{v_data.get('iso_abd_cadera_der', 0)} N")
                with ci8: kpi_compacto("Abducción Cadera (I)", f"{v_data.get('iso_abd_cadera_izq', 0)} N")
                
                asi_ext = calcular_asimetria(v_data.get('iso_ext_rodilla_der', 0), v_data.get('iso_ext_rodilla_izq', 0))
                asi_flx = calcular_asimetria(v_data.get('iso_flex_rodilla_der', 0), v_data.get('iso_flex_rodilla_izq', 0))
                
                cai1, cai2 = st.columns(2)
                cai1.info(f"**Asimetría Extensión de Cuádriceps:** {badge_asi(asi_ext)}")
                cai2.info(f"**Asimetría Flexión de Isquiosurales:** {badge_asi(asi_flx)}")
                
                flx_d, ext_d = v_data.get('iso_flex_rodilla_der', 0), v_data.get('iso_ext_rodilla_der', 0)
                flx_i, ext_i = v_data.get('iso_flex_rodilla_izq', 0), v_data.get('iso_ext_rodilla_izq', 0)
                ratio_hq_d = round(flx_d / ext_d, 2) if ext_d > 0 else 0
                ratio_hq_i = round(flx_i / ext_i, 2) if ext_i > 0 else 0
                
                add_d, abd_d = v_data.get('iso_add_cadera_der', 0), v_data.get('iso_abd_cadera_der', 0)
                add_i, abd_i = v_data.get('iso_add_cadera_izq', 0), v_data.get('iso_abd_cadera_izq', 0)
                ratio_adab_d = round(add_d / abd_d, 2) if abd_d > 0 else 0
                ratio_adab_i = round(add_i / abd_i, 2) if abd_i > 0 else 0
                
                cr1, cr2, cr3, cr4 = st.columns(4)
                with cr1: st.info(f"**Isquiosurales / Cuádriceps (D):**\n{badge_hq(ratio_hq_d)}")
                with cr2: st.info(f"**Isquiosurales / Cuádriceps (I):**\n{badge_hq(ratio_hq_i)}")
                with cr3: st.info(f"**Aductores / Abductores (D):**\n{badge_adab(ratio_adab_d)}")
                with cr4: st.info(f"**Aductores / Abductores (I):**\n{badge_adab(ratio_adab_i)}")

                st.markdown("---")

                # ---------------------------------------------------------
                # 4. FUERZA MÁXIMA
                # ---------------------------------------------------------
                st.markdown("#### 🏋️‍♂️ 4. Fuerza Máxima Estimada")
                sq_rm = v_data.get('rm_sentadilla', 0.0)
                dl_rm = v_data.get('rm_peso_muerto', 0.0)
                
                crm1, crm2 = st.columns(2)
                with crm1: kpi_compacto("Estimación 1RM Sentadilla", f"{sq_rm} kg")
                with crm2: kpi_compacto("Estimación 1RM Peso Muerto", f"{dl_rm} kg")
                
                if sq_rm > 0 or dl_rm > 0:
                    cz1, cz2 = st.columns(2)
                    with cz1:
                        st.markdown("*Zonas de Carga de Ejercicios Básicos*")
                        df_zonas = pd.DataFrame({
                            "Intensidad": ["100% (1RM)", "90%", "80%", "70%", "60%"],
                            "Sentadilla (kg)": [sq_rm, round(sq_rm*0.9,1), round(sq_rm*0.8,1), round(sq_rm*0.7,1), round(sq_rm*0.6,1)],
                            "Peso Muerto (kg)": [dl_rm, round(dl_rm*0.9,1), round(dl_rm*0.8,1), round(dl_rm*0.7,1), round(dl_rm*0.6,1)]
                        })
                        st.dataframe(df_zonas, hide_index=True)
                    
                    with cz2:
                        st.markdown("*Estimación para Ejercicios Accesorios*")
                        df_acc = pd.DataFrame({
                            "Ejercicio Accesorio": ["Empuje de Cadera", "Peso Muerto Asimétrico", "Sentadilla Búlgara", "Zancada", "Peso Muerto Rumano Unilateral"],
                            "Estimación (kg)": [
                                round(sq_rm * 1.20, 1),
                                round(dl_rm * 0.70, 1),
                                round(sq_rm * 0.50, 1),
                                round(sq_rm * 0.45, 1),
                                round(dl_rm * 0.45, 1)
                            ]
                        })
                        st.dataframe(df_acc, hide_index=True)
                else:
                    st.info("No se registraron datos válidos en esta valoración para calcular las proyecciones.")

# ==========================================
# PESTAÑA 3: TABLA DE REGISTROS
# ==========================================
with tab_reg:
    st.markdown("### 📋 Tabla de Registros Generales")
    if not valoraciones:
        st.info("No hay valoraciones registradas todavía.")
    else:
        df_vals_completos = pd.DataFrame(valoraciones)
        df_vals_completos['Deportista'] = df_vals_completos['jugador_id'].map(mapa_jugadores)
        
        renombres = {
            'fecha': 'Fecha', 'temporada': 'Temporada', 'numero_valoracion': 'Nº Val.', 'Deportista': 'Deportista', 'lesion': 'Lesión',
            'fms_sentadilla': 'FMS Sentadilla', 
            'fms_paso_obstaculo_der': 'FMS Paso Obst. (Der)', 'fms_paso_obstaculo_izq': 'FMS Paso Obst. (Izq)',
            'fms_zancada_der': 'FMS Zancada (Der)', 'fms_zancada_izq': 'FMS Zancada (Izq)', 
            'fms_mov_hombro_der': 'FMS Hombro (Der)', 'fms_mov_hombro_izq': 'FMS Hombro (Izq)', 
            'fms_elevacion_pierna_der': 'FMS Elev. Pierna (Der)', 'fms_elevacion_pierna_izq': 'FMS Elev. Pierna (Izq)',
            'fms_estabilidad_tronco': 'FMS Estab. Tronco', 'fms_estabilidad_rotatoria': 'FMS Estab. Rotatoria',
            'cmj_bilateral': 'CMJ Bilateral (cm)', 'cmj_uni_der': 'CMJ Uni. (Der)', 'cmj_uni_izq': 'CMJ Uni. (Izq)',
            'salto_horiz_der': 'Salto Horiz. (Der)', 'salto_horiz_izq': 'Salto Horiz. (Izq)',
            'iso_ext_rodilla_der': 'Iso Ext. Rodilla Der (N)', 'iso_ext_rodilla_izq': 'Iso Ext. Rodilla Izq (N)',
            'iso_flex_rodilla_der': 'Iso Flex. Rodilla Der (N)', 'iso_flex_rodilla_izq': 'Iso Flex. Rodilla Izq (N)',
            'iso_add_cadera_der': 'Iso Add. Cadera Der (N)', 'iso_add_cadera_izq': 'Iso Add. Cadera Izq (N)',
            'iso_abd_cadera_der': 'Iso Abd. Cadera Der (N)', 'iso_abd_cadera_izq': 'Iso Abd. Cadera Izq (N)',
            'rm_sentadilla': '1RM Sentadilla (kg)', 'rm_peso_muerto': '1RM Peso Muerto (kg)', 'comentarios': 'Comentarios'
        }
        
        cols_base = ['Deportista', 'Fecha', 'Temporada', 'Nº Val.', 'Lesión']
        df_vals_completos = df_vals_completos.rename(columns=renombres)
        cols_existentes = [c for c in df_vals_completos.columns if c in renombres.values()]
        resto_cols = [c for c in cols_existentes if c not in cols_base]
        orden_final = cols_base + resto_cols
        
        st.data_editor(df_vals_completos[orden_final], use_container_width=True, hide_index=True)
