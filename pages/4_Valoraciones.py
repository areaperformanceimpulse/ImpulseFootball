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

# 1. REORDEN DE PESTAÑAS (Tabla de registros al final)
tab_nuevo, tab_informes, tab_reg = st.tabs(["➕ Añadir Nueva Valoración", "📈 Informes de valoraciones", "📋 Tabla de registros"])

jugadores = st.session_state.get("jugadores", [])
valoraciones = st.session_state.get("valoraciones", [])
mapa_jugadores = {j['id']: j['nombre'] for j in jugadores}

# ==========================================
# PESTAÑA 1: AÑADIR NUEVA VALORACIÓN
# ==========================================
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
            
            # --- 1. MOVILIDAD (FMS) ---
            st.markdown("#### 🤸 1. Protocolo FMS (Movilidad y Estabilidad - Puntuación 0 a 3)")
            
            def tarjeta_fms_numerica(titulo, es_unilateral=True):
                st.markdown(f"**{titulo}**")
                if es_unilateral:
                    cd, ci = st.columns(2)
                    with cd: val_d = st.number_input(f"Der.", min_value=0, max_value=3, value=3, step=1, key=f"fms_{titulo}_der")
                    with ci: val_i = st.number_input(f"Izq.", min_value=0, max_value=3, value=3, step=1, key=f"fms_{titulo}_izq")
                    return val_d, val_i
                else:
                    val = st.number_input(f"(Bilateral)", min_value=0, max_value=3, value=3, step=1, key=f"fms_{titulo}_bi")
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
            
            # --- 2. SALTO ---
            st.markdown("#### 🦘 2. Test de Salto")
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.markdown("**CMJ Bilateral (cm)**")
                cmj_bi = st.number_input("Altura CMJ", min_value=0.0, value=0.0, step=0.5, label_visibility="collapsed")
            with col_s2:
                st.markdown("**CMJ Unilateral (cm)**")
                cmj_ud = st.number_input("CMJ Unilateral Derecha", min_value=0.0, value=0.0, step=0.5)
                cmj_ui = st.number_input("CMJ Unilateral Izquierda", min_value=0.0, value=0.0, step=0.5)
            with col_s3:
                st.markdown("**Salto Horizontal (cm)**")
                sh_d = st.number_input("Salto Horiz. Derecha", min_value=0.0, value=0.0, step=1.0)
                sh_i = st.number_input("Salto Horiz. Izquierda", min_value=0.0, value=0.0, step=1.0)

            st.markdown("---")
            
            # --- 3. ISOMETRÍA ---
            st.markdown("#### ⚡ 3. Fuerza Máxima Isométrica (N)")
            ci1, ci2 = st.columns(2)
            with ci1:
                st.markdown("**Extensión de Rodilla (N) - Cuádriceps**")
                iso_ext_d = st.number_input("Ext. Rodilla Derecha", min_value=0.0, value=0.0, step=1.0)
                iso_ext_i = st.number_input("Ext. Rodilla Izquierda", min_value=0.0, value=0.0, step=1.0)
                
                st.markdown("**Aductores de Cadera (N)**")
                iso_add_d = st.number_input("Aductores Derecha", min_value=0.0, value=0.0, step=1.0)
                iso_add_i = st.number_input("Aductores Izquierda", min_value=0.0, value=0.0, step=1.0)
            with ci2:
                st.markdown("**Flexión de Rodilla (N) - Isquiosurales**")
                iso_flx_d = st.number_input("Flex. Rodilla Derecha", min_value=0.0, value=0.0, step=1.0)
                iso_flx_i = st.number_input("Flex. Rodilla Izquierda", min_value=0.0, value=0.0, step=1.0)
                
                st.markdown("**Abductores de Cadera (N)**")
                iso_abd_d = st.number_input("Abductores Derecha", min_value=0.0, value=0.0, step=1.0)
                iso_abd_i = st.number_input("Abductores Izquierda", min_value=0.0, value=0.0, step=1.0)

            st.markdown("---")
            
            # --- 4. ESTIMACIÓN 1RM (5 SERIES: PESO Y VELOCIDAD) ---
            st.markdown("#### 🏋️‍♂️ 4. Estimación 1RM (5 Series de Carga y Velocidad)")
            st.markdown("<small style='color: #64748b;'>Introduce los kg y la velocidad del encoder. El valor se calculará al pulsar el botón o guardar.</small>", unsafe_allow_html=True)

            def inputs_5_series(nombre_ejercicio, key_prefix):
                st.markdown(f"**{nombre_ejercicio}**")
                p_list, v_list = [], []
                for s in range(1, 6):
                    c1, c2 = st.columns(2)
                    with c1:
                        p = st.number_input(f"Serie {s} - Kg", min_value=0.0, value=0.0, step=2.5, key=f"{key_prefix}_p_{s}")
                    with c2:
                        v = st.number_input(f"Serie {s} - Velocidad m/s", min_value=0.0, value=0.0, step=0.01, key=f"{key_prefix}_v_{s}")
                    p_list.append(p)
                    v_list.append(v)
                return p_list, v_list

            cr1, cr2 = st.columns(2)
            with cr1:
                p_sq, v_sq = inputs_5_series("Sentadilla", "sq")
            with cr2:
                p_pm, v_pm = inputs_5_series("Peso Muerto", "pm")

            # Cálculo automático seguro basado en la serie con mayor carga con velocidad válida (> 0)
            def calcular_rm_final(pesos, vels):
                validas = [(pesos[i], vels[i]) for i in range(5) if vels[i] > 0 and pesos[i] > 0]
                if validas:
                    p_max, v_max = max(validas, key=lambda x: x[0])
                    return round(p_max / v_max, 1) # Fórmula básica de estimación 1RM (Carga / Velocidad relativa)
                return round(max(pesos), 1) if max(pesos) > 0 else 0.0

            rm_sq = calcular_rm_final(p_sq, v_sq)
            rm_pm = calcular_rm_final(p_pm, v_pm)

            st.info(f"💡 **1RM Estimado Actual — Sentadilla:** {rm_sq} kg | **Peso Muerto:** {rm_pm} kg")

            st.markdown("---")
            comentarios = st.text_area("Observaciones Generales de la Valoración:")
            
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
        # Filtros en línea
        cf1, cf2, cf3 = st.columns(3)
        with cf1:
            jug_sel_prog = st.selectbox("Deportista:", options=list(mapa_jugadores.keys()), format_func=lambda x: mapa_jugadores[x])
        
        vals_jugador = [v for v in valoraciones if v.get('jugador_id') == jug_sel_prog]
        
        if not vals_jugador:
            st.warning("Este deportista todavía no tiene valoraciones registradas.")
        else:
            df_pj = pd.DataFrame(vals_jugador)
            temporadas = df_pj['temporada'].dropna().unique().tolist()
            
            with cf2:
                temp_sel = st.selectbox("Temporada:", options=temporadas)
            
            df_temp = df_pj[df_pj['temporada'] == temp_sel]
            
            if df_temp.empty:
                st.warning("No hay valoraciones en esta temporada.")
            else:
                # Diccionario para formatear: "Nº (Fecha)"
                dicc_vals = {row['id']: f"{row['numero_valoracion']} ({row['fecha']})" for idx, row in df_temp.iterrows()}
                
                with cf3:
                    val_sel_id = st.selectbox("Nº de Valoración:", options=list(dicc_vals.keys()), format_func=lambda x: dicc_vals[x])
                
                # Datos de la valoración seleccionada
                v_data = df_temp[df_temp['id'] == val_sel_id].iloc[0]
                
                def badge_asi(val):
                    if val < 10: return f"🟢 {val}% (Óptimo)"
                    elif val <= 15: return f"🟡 {val}% (Atención)"
                    else: return f"🔴 {val}% (Riesgo)"

                st.markdown(f"#### 🔎 Análisis de Simetría y Ratios Lesionales - {mapa_jugadores[jug_sel_prog]}")
                
                # --- METRICAS DE SALTO Y FUERZA ---
                c_inf1, c_inf2 = st.columns(2)
                
                with c_inf1:
                    st.markdown("**🦘 Saltos Unilaterales**")
                    asi_cmj = calcular_asimetria(v_data.get('cmj_uni_der',0), v_data.get('cmj_uni_izq',0))
                    asi_sh = calcular_asimetria(v_data.get('salto_horiz_der',0), v_data.get('salto_horiz_izq',0))
                    st.write(f"- **Asimetría CMJ Unilateral:** {badge_asi(asi_cmj)}")
                    st.write(f"- **Asimetría Salto Horizontal:** {badge_asi(asi_sh)}")
                
                with c_inf2:
                    st.markdown("**⚡ Fuerza Isométrica**")
                    asi_ext = calcular_asimetria(v_data.get('iso_ext_rodilla_der',0), v_data.get('iso_ext_rodilla_izq',0))
                    asi_flx = calcular_asimetria(v_data.get('iso_flex_rodilla_der',0), v_data.get('iso_flex_rodilla_izq',0))
                    st.write(f"- **Asimetría Extensión (Cuádriceps):** {badge_asi(asi_ext)}")
                    st.write(f"- **Asimetría Flexión (Isquiosurales):** {badge_asi(asi_flx)}")
                
                st.markdown("---")
                
                # --- RATIOS DE PREVENCIÓN ---
                st.markdown("#### 🛡️ Ratios Clínicos de Prevención Lesional")
                cr1, cr2 = st.columns(2)
                
                # Ratio H/Q (Isquio/Cuad)
                flx_d, ext_d = v_data.get('iso_flex_rodilla_der',0), v_data.get('iso_ext_rodilla_der',0)
                flx_i, ext_i = v_data.get('iso_flex_rodilla_izq',0), v_data.get('iso_ext_rodilla_izq',0)
                
                ratio_hq_d = round(flx_d / ext_d, 2) if ext_d > 0 else 0
                ratio_hq_i = round(flx_i / ext_i, 2) if ext_i > 0 else 0
                
                def badge_hq(val): return f"🟢 {val}" if val >= 0.6 else f"🔴 {val} (Déficit isquio)"
                
                with cr1:
                    st.markdown("**Ratio Isquio/Cuádriceps (H/Q)**")
                    st.caption("Recomendación: > 0.60 para prevenir lesiones isquiosurales.")
                    st.write(f"- **Pierna Derecha:** {badge_hq(ratio_hq_d)}")
                    st.write(f"- **Pierna Izquierda:** {badge_hq(ratio_hq_i)}")
                
                # Ratio ADD/ABD
                add_d, abd_d = v_data.get('iso_add_cadera_der',0), v_data.get('iso_abd_cadera_der',0)
                add_i, abd_i = v_data.get('iso_add_cadera_izq',0), v_data.get('iso_abd_cadera_izq',0)
                
                ratio_adab_d = round(add_d / abd_d, 2) if abd_d > 0 else 0
                ratio_adab_i = round(add_i / abd_i, 2) if abd_i > 0 else 0
                
                def badge_adab(val): return f"🟢 {val}" if val >= 0.9 else f"🔴 {val} (Déficit Aductor)"
                
                with cr2:
                    st.markdown("**Ratio Aductor/Abductor**")
                    st.caption("Recomendación: > 0.90 para prevenir pubalgias/lesión aductor.")
                    st.write(f"- **Pierna Derecha:** {badge_adab(ratio_adab_d)}")
                    st.write(f"- **Pierna Izquierda:** {badge_adab(ratio_adab_i)}")
                
                st.markdown("---")
                
                # --- PERFIL 1RM Y ESTIMACIONES ---
                st.markdown("#### 🏋️‍♂️ Perfil de Cargas (1RM) y Proyecciones")
                sq_rm = v_data.get('rm_sentadilla', 0.0)
                dl_rm = v_data.get('rm_peso_muerto', 0.0)
                
                if sq_rm > 0 or dl_rm > 0:
                    cz1, cz2 = st.columns(2)
                    with cz1:
                        st.markdown("**Zonas de Carga (Básicos)**")
                        df_zonas = pd.DataFrame({
                            "Intensidad": ["100% (1RM)", "90%", "80%", "70%", "60%"],
                            "Sentadilla (kg)": [sq_rm, round(sq_rm*0.9,1), round(sq_rm*0.8,1), round(sq_rm*0.7,1), round(sq_rm*0.6,1)],
                            "Peso Muerto (kg)": [dl_rm, round(dl_rm*0.9,1), round(dl_rm*0.8,1), round(dl_rm*0.7,1), round(dl_rm*0.6,1)]
                        })
                        st.dataframe(df_zonas, hide_index=True)
                    
                    with cz2:
                        st.markdown("**Estimación Ejercicios Accesorios (1RM)**")
                        st.caption("Basado en % bibliográficos derivados del Bilateral.")
                        df_acc = pd.DataFrame({
                            "Ejercicio": ["Hip Thrust", "Peso Muerto Asimétrico", "Sentadilla Búlgara (por pierna)", "Zancada (por pierna)", "RDL Unilateral (por pierna)"],
                            "Referencia": ["120% SQ", "70% DL", "50% SQ", "45% SQ", "45% DL"],
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
                    st.info("No se registraron datos de 1RM en esta valoración para proyectar cargas.")

# ==========================================
# PESTAÑA 3: TABLA DE REGISTROS (AL FINAL, COMPLETA Y EDITABLE)
# ==========================================
with tab_reg:
    st.markdown("### 📋 Tabla de Registros Generales")
    if not valoraciones:
        st.info("No hay valoraciones registradas todavía.")
    else:
        df_vals_completos = pd.DataFrame(valoraciones)
        df_vals_completos['Deportista'] = df_vals_completos['jugador_id'].map(mapa_jugadores)
        
        # Mapeo para nombres de columnas profesionales y completos
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
        
        # Reordenar para que Deportista salga primero
        cols_base = ['Deportista', 'Fecha', 'Temporada', 'Nº Val.', 'Lesión']
        
        df_vals_completos = df_vals_completos.rename(columns=renombres)
        cols_existentes = [c for c in df_vals_completos.columns if c in renombres.values()]
        
        # Asegurar el orden visual
        resto_cols = [c for c in cols_existentes if c not in cols_base]
        orden_final = cols_base + resto_cols
        
        # Tabla Editable
        st.data_editor(df_vals_completos[orden_final], use_container_width=True, hide_index=True)
