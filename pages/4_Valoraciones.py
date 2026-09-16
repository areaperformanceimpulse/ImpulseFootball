import streamlit as st
from database.db_manager import supabase, cargar_datos_sistema
from utils.math_helpers import aplicar_estilos_base, calcular_asimetria, safe_float
from datetime import date
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Valoraciones - ImpulseFootball", page_icon="📊", layout="wide")
aplicar_estilos_base()

if not st.session_state.get("autenticado", False):
    st.warning("Sesión caducada.")
    st.stop()

cargar_datos_sistema()

st.title("📊 Valoraciones Condicionales (Gimnasio)")

tab_informes, tab_nuevo, tab_reg = st.tabs(["📈 Informes de valoraciones", "➕ Añadir Nueva Valoración", "📋 Tabla de registros"])

jugadores = st.session_state.get("jugadores", [])
valoraciones = st.session_state.get("valoraciones", [])
mapa_jugadores = {j['id']: j['nombre'] for j in jugadores}

# ==========================================
# FUNCIONES DE AUTOMATIZACIÓN DE TIEMPO
# ==========================================
def obtener_temporada(fecha_obj):
    """Calcula la temporada (ej: '26/27') a partir de una fecha. Inicia el 1 de septiembre."""
    mes = fecha_obj.month
    anio = fecha_obj.year
    if mes >= 9:
        # Del 1 de septiembre hasta final de año (ej: sep 2026 -> 26/27)
        return f"{str(anio)[-2:]}/{str(anio + 1)[-2:]}"
    else:
        # De enero a agosto (ej: ago 2027 -> 26/27)
        return f"{str(anio - 1)[-2:]}/{str(anio)[-2:]}"

def calcular_num_valoracion(jugador_id, temporada_str, vals_existentes, id_excluir=None):
    """Cuenta cuántas valoraciones tiene un jugador en una temporada para asignar el número correlativo."""
    count = 0
    for v in vals_existentes:
        if v.get('jugador_id') == jugador_id and v.get('temporada') == temporada_str:
            if id_excluir is None or v.get('id') != id_excluir:
                count += 1
    return count + 1

# ==========================================
# PESTAÑA 1: INFORMES DE VALORACIONES
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
                
                with cf3: 
                    val_sel_id = st.selectbox("Número de Valoración:", options=[None] + list(dicc_vals.keys()), format_func=lambda x: dicc_vals[x] if x else "Seleccione para generar...")
                
                if val_sel_id is None:
                    st.info("👆 Selecciona una valoración en el menú superior para desplegar el informe exhaustivo.")
                else:
                    v_data = df_temp[df_temp['id'] == val_sel_id].iloc[0]
                    peso_actual = safe_float(v_data.get('peso_corporal'))
                    if peso_actual == 0: peso_actual = 70.0 
                    
                    def tarjeta_kpi(titulo, valor, subtitulo=""):
                        st.markdown(f"""
                        <div style='background-color: white; padding: 15px; border-radius: 8px; border-left: 5px solid #10833d; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 15px; border-right: 1px solid #eee; border-top: 1px solid #eee; border-bottom: 1px solid #eee;'>
                            <div style='font-size: 0.80em; color: #64748b; font-weight: 600; text-transform: uppercase;'>{titulo}</div>
                            <div style='font-size: 1.4em; font-weight: 800; color: #09274e;'>{valor}</div>
                            {f"<div style='font-size: 0.8em; color: #64748b; margin-top: 4px;'>{subtitulo}</div>" if subtitulo else ""}
                        </div>
                        """, unsafe_allow_html=True)

                    def tarjeta_kpi_doble(titulo, val_d, val_i, lbl_d="Der", lbl_i="Izq"):
                        st.markdown(f"""
                        <div style='background-color: white; padding: 15px; border-radius: 8px; border-left: 5px solid #09274e; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 15px; border-right: 1px solid #eee; border-top: 1px solid #eee; border-bottom: 1px solid #eee;'>
                            <div style='font-size: 0.80em; color: #64748b; font-weight: 600; text-transform: uppercase; margin-bottom: 8px;'>{titulo}</div>
                            <div style='display: flex; justify-content: space-between;'>
                                <div><span style='font-size: 0.85em; color: #64748b;'>{lbl_d}:</span> <span style='font-size: 1.2em; font-weight: 800; color: #10833d;'>{val_d}</span></div>
                                <div><span style='font-size: 0.85em; color: #64748b;'>{lbl_i}:</span> <span style='font-size: 1.2em; font-weight: 800; color: #10833d;'>{val_i}</span></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    def badge_asi_detallado(val, der, izq):
                        if val < 10: 
                            return f"🟢 {val}% (Óptimo)"
                        else:
                            pierna_debil = "Derecha" if safe_float(der) < safe_float(izq) else ("Izquierda" if safe_float(izq) < safe_float(der) else "Ninguna")
                            if val <= 15: 
                                return f"🟡 {val}% (Precaución | Débil: {pierna_debil})"
                            else: 
                                return f"🔴 {val}% (Riesgo | Débil: {pierna_debil})"

                    def badge_hq(val): return f"🟢 {val}" if val >= 0.6 else f"🔴 {val} (Déficit)"
                    def badge_adab(val): return f"🟢 {val}" if val >= 0.9 else f"🔴 {val} (Déficit)"
                                      
                    def generar_grafico_radar(val_inicial, val_actual, peso_corp):
                        peso = peso_corp if peso_corp > 0 else 70.0
                        def calcular_porcentajes_optimos(v):
                            if not v: return [0, 0, 0, 0, 0]
                            fms_mov = sum([v.get('fms_mov_hombro_der', 0), v.get('fms_mov_hombro_izq', 0), v.get('fms_elevacion_pierna_der', 0), v.get('fms_elevacion_pierna_izq', 0)])
                            p_mov = min(100, round((fms_mov / 12.0) * 100))
                            
                            cmj = v.get('cmj_bilateral', 0)
                            p_cmj = min(100, round((cmj / 50.0) * 100))
                            
                            isq_d, isq_i = v.get('iso_flex_rodilla_der', 0), v.get('iso_flex_rodilla_izq', 0)
                            isq_prom = (isq_d + isq_i) / 2 if (isq_d > 0 or isq_i > 0) else 0
                            p_isq = min(100, round(((isq_prom / peso) / 4.5) * 100))
                            
                            sq_rm = v.get('rm_sentadilla', 0)
                            p_sq = min(100, round(((sq_rm / peso) / 2.0) * 100))
                            
                            sh_d, sh_i = v.get('salto_horiz_der', 0), v.get('salto_horiz_izq', 0)
                            sh_prom = (sh_d + sh_i) / 2 if (sh_d > 0 or sh_i > 0) else 0
                            p_sh = min(100, round((sh_prom / 240.0) * 100))
                            
                            return [p_mov, p_cmj, p_isq, p_sq, p_sh]
                    
                        categorias = ['Movilidad FMS', 'Salto (CMJ)', 'F. Isquio (N/kg)', 'F. Sentadilla (Rel)', 'Salto Horiz.']
                        df_radar = pd.DataFrame({
                            'Métrica': categorias * 2,
                            'Valor': calcular_porcentajes_optimos(val_inicial) + calcular_porcentajes_optimos(val_actual),
                            'Test': ['Inicial (Base)'] * 5 + ['Actual'] * 5
                        })
                        
                        fig = px.line_polar(df_radar, r='Valor', theta='Métrica', color='Test', line_close=True, color_discrete_map={'Inicial (Base)': '#09274e', 'Actual': '#10833d'})
                        fig.update_traces(fill='toself', opacity=0.4)
                        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=350, margin=dict(l=20, r=20, t=30, b=20))
                        return fig
                    
                    def generar_recomendaciones_automaticas(v_data):
                        alertas = []
                        peso = v_data.get('peso_corporal', 70) if v_data.get('peso_corporal', 70) > 0 else 70
                        isq_d, isq_i = v_data.get('iso_flex_rodilla_der', 0), v.get('iso_flex_rodilla_izq', 0)
                        
                        if (isq_d / peso) < 3.5 or (isq_i / peso) < 3.5:
                            min_isq = round(min(isq_d / peso, isq_i / peso), 2)
                            alertas.append(f"⚠️ **Déficit de fuerza en isquiosurales** ({min_isq} N/kg frente al umbral óptimo de 3.5 N/kg). **Pauta:** Priorizar trabajo excéntrico (Nordic Curl) y cadenas posteriores.")
                    
                        cmj_d, cmj_i = v_data.get('cmj_uni_der', 0), v_data.get('cmj_uni_izq', 0)
                        if cmj_d > 0 and cmj_i > 0:
                            max_cmj = max(cmj_d, cmj_i)
                            min_cmj = min(cmj_d, cmj_i)
                            asi_cmj = round(abs(max_cmj - min_cmj) / max_cmj * 100, 1)
                            pierna_debil = "Derecha" if cmj_d < cmj_i else "Izquierda"
                            if asi_cmj > 10:
                                alertas.append(f"⚠️ **Asimetría unilateral de salto del {asi_cmj}%** con afectación en hemicuerpo {pierna_debil}. **Pauta:** Introducir bloques de fuerza unilateral y control motor específico.")
                    
                        if not alertas:
                            st.success("🟢 **Perfil Físico Estable:** No se detectan déficits críticos ni riesgos lesionales destacados en los test evaluados.")
                        else:
                            st.markdown("#### 🤖 Pautas y Recomendaciones Automatizadas del Staff")
                            for alerta in alertas:
                                st.warning(alerta)
                                
                    st.markdown("---")
                    
                    st.markdown("#### 🤸 1. Análisis de Movilidad y Estabilidad")
                    cm1, cm2, cm3 = st.columns(3)
                    with cm1: tarjeta_kpi("FMS 1: Sentadilla profunda", v_data.get('fms_sentadilla', 0))
                    with cm2: tarjeta_kpi_doble("FMS 2: Paso Obstáculo", v_data.get('fms_paso_obstaculo_der', 0), v_data.get('fms_paso_obstaculo_izq', 0))
                    with cm3: tarjeta_kpi_doble("FMS 3: Zancada en línea", v_data.get('fms_zancada_der', 0), v_data.get('fms_zancada_izq', 0))
                    
                    cm4, cm5, cm6, cm7 = st.columns(4)
                    with cm4: tarjeta_kpi_doble("FMS 4: Mov. Hombro", v_data.get('fms_mov_hombro_der', 0), v_data.get('fms_mov_hombro_izq', 0))
                    with cm5: tarjeta_kpi_doble("FMS 5: Elev. Pierna", v_data.get('fms_elevacion_pierna_der', 0), v_data.get('fms_elevacion_pierna_izq', 0))
                    with cm6: tarjeta_kpi("FMS 6: Est. Tronco", v_data.get('fms_estabilidad_tronco', 0))
                    with cm7: tarjeta_kpi("FMS 7: Est. Rotatoria", v_data.get('fms_estabilidad_rotatoria', 0))

                    mov_total = sum([v_data.get('fms_mov_hombro_der',0), v_data.get('fms_mov_hombro_izq',0), v_data.get('fms_elevacion_pierna_der',0), v_data.get('fms_elevacion_pierna_izq',0)])
                    ctrl_total = sum([v_data.get('fms_sentadilla',0), v_data.get('fms_estabilidad_tronco',0), v_data.get('fms_estabilidad_rotatoria',0), v_data.get('fms_paso_obstaculo_der',0), v_data.get('fms_paso_obstaculo_izq',0), v_data.get('fms_zancada_der',0), v_data.get('fms_zancada_izq',0)])
                    
                    if mov_total >= 10: mov_badge = "🟢 Óptimo"
                    elif mov_total >= 8: mov_badge = "🟡 Aceptable"
                    else: mov_badge = "🔴 Deficiente"
                    
                    if ctrl_total >= 16: ctrl_badge = "🟢 Óptimo"
                    elif ctrl_total >= 14: ctrl_badge = "🟡 Aceptable"
                    else: ctrl_badge = "🔴 Deficiente"

                    c_fms1, c_fms2 = st.columns(2)
                    c_fms1.info(f"**Clúster Movilidad:** {mov_total} / 12 pts | {mov_badge}\n\n*(Valora la flexibilidad y longitud del tejido)*")
                    c_fms2.info(f"**Clúster Control Motor:** {ctrl_total} / 21 pts | {ctrl_badge}\n\n*(Valora la estabilización activa de las articulaciones)*")

                    st.markdown("---")
                    
                    st.markdown("#### 🦘 2. Rendimiento en Salto y Vectores")
                    cs1, cs2, cs3 = st.columns(3)
                    with cs1: tarjeta_kpi("Salto Vertical Bilateral", f"{v_data.get('cmj_bilateral', 0)} cm")
                    with cs2: tarjeta_kpi_doble("Salto Vertical Unilateral", f"{v_data.get('cmj_uni_der', 0)} cm", f"{v_data.get('cmj_uni_izq', 0)} cm")
                    with cs3: tarjeta_kpi_doble("Salto Horizontal", f"{v_data.get('salto_horiz_der', 0)} cm", f"{v_data.get('salto_horiz_izq', 0)} cm")
                    
                    cmj_d, cmj_i = v_data.get('cmj_uni_der', 0), v_data.get('cmj_uni_izq', 0)
                    asi_cmj = calcular_asimetria(cmj_d, cmj_i)
                    
                    cmj_bi = safe_float(v_data.get('cmj_bilateral', 0))
                    cmj_uni_sum = safe_float(cmj_d) + safe_float(cmj_i)
                    dbl = round(100 * (cmj_bi / cmj_uni_sum) - 100, 1) if cmj_uni_sum > 0 else 0
                    
                    if dbl < -10: dbl_txt = f"🟢 {dbl}% (Óptimo - Perfil unilateral de alta eficiencia para fútbol)"
                    elif dbl < 0: dbl_txt = f"🟡 {dbl}% (Adecuado - Eficiencia unilateral estándar)"
                    else: dbl_txt = f"🔴 {dbl}% (Déficit Unilateral - Riesgo de lentitud en sprints y recortes)"
                    
                    sh_promedio = (safe_float(v_data.get('salto_horiz_der', 0)) + safe_float(v_data.get('salto_horiz_izq', 0))) / 2
                    cmj_uni_promedio = cmj_uni_sum / 2
                    ratio_vectores = round(sh_promedio / cmj_uni_promedio, 2) if cmj_uni_promedio > 0 else 0
                    
                    if ratio_vectores > 4.5: perfil_vector = "🏃 Dominancia Horizontal (Perfil Acelerador - 1ºs metros)"
                    elif ratio_vectores > 0 and ratio_vectores < 3.5: perfil_vector = "🚀 Dominancia Vertical (Perfil Aéreo y Velocidad Punta)"
                    elif ratio_vectores >= 3.5 and ratio_vectores <= 4.5: perfil_vector = "⚖️ Perfil Vectorial Equilibrado"
                    else: perfil_vector = "Datos insuficientes"
                    
                    ca1, ca2, ca3 = st.columns(3)
                    ca1.info(f"**Asimetría Vertical:** {badge_asi_detallado(asi_cmj, cmj_d, cmj_i)}")
                    ca2.info(f"**Déficit Bilateral (DBL):**\n\n{dbl_txt}")
                    ca3.info(f"**Teoría de Vectores (Ratio H/V):** {ratio_vectores}\n\n{perfil_vector}")

                    st.markdown("---")

                    st.markdown("#### ⚡ 3. Fuerza Máxima Isométrica y Fuerza Relativa")
                    ci1, ci2, ci3, ci4 = st.columns(4)
                    with ci1: tarjeta_kpi_doble("Extensión (Cuád)", f"{v_data.get('iso_ext_rodilla_der', 0)} N", f"{v_data.get('iso_ext_rodilla_izq', 0)} N")
                    with ci2: tarjeta_kpi_doble("Flexión (Isq)", f"{v_data.get('iso_flex_rodilla_der', 0)} N", f"{v_data.get('iso_flex_rodilla_izq', 0)} N")
                    with ci3: tarjeta_kpi_doble("Aducción", f"{v_data.get('iso_add_cadera_der', 0)} N", f"{v_data.get('iso_add_cadera_izq', 0)} N")
                    with ci4: tarjeta_kpi_doble("Abducción", f"{v_data.get('iso_abd_cadera_der', 0)} N", f"{v_data.get('iso_abd_cadera_izq', 0)} N")
                    
                    ext_d, ext_i = v_data.get('iso_ext_rodilla_der', 0), v_data.get('iso_ext_rodilla_izq', 0)
                    flx_d, flx_i = v_data.get('iso_flex_rodilla_der', 0), v_data.get('iso_flex_rodilla_izq', 0)
                    
                    asi_ext = calcular_asimetria(ext_d, ext_i)
                    asi_flx = calcular_asimetria(flx_d, flx_i)
                    
                    cai1, cai2 = st.columns(2)
                    cai1.info(f"**Asimetría Extensión de Cuádriceps:** {badge_asi_detallado(asi_ext, ext_d, ext_i)}")
                    cai2.info(f"**Asimetría Flexión de Isquiosurales:** {badge_asi_detallado(asi_flx, flx_d, flx_i)}")
                    
                    ratio_hq_d = round(safe_float(flx_d) / safe_float(ext_d), 2) if safe_float(ext_d) > 0 else 0
                    ratio_hq_i = round(safe_float(flx_i) / safe_float(ext_i), 2) if safe_float(ext_i) > 0 else 0
                    
                    add_d, abd_d = v_data.get('iso_add_cadera_der', 0), v_data.get('iso_abd_cadera_der', 0)
                    add_i, abd_i = v_data.get('iso_add_cadera_izq', 0), v_data.get('iso_abd_cadera_izq', 0)
                    ratio_adab_d = round(safe_float(add_d) / safe_float(abd_d), 2) if safe_float(abd_d) > 0 else 0
                    ratio_adab_i = round(safe_float(add_i) / safe_float(abd_i), 2) if safe_float(abd_i) > 0 else 0
    
                    f_rel_ext_d = round(safe_float(ext_d) / peso_actual, 2) if peso_actual > 0 else 0
                    f_rel_ext_i = round(safe_float(ext_i) / peso_actual, 2) if peso_actual > 0 else 0
                    f_rel_flx_d = round(safe_float(flx_d) / peso_actual, 2) if peso_actual > 0 else 0
                    f_rel_flx_i = round(safe_float(flx_i) / peso_actual, 2) if peso_actual > 0 else 0
    
                    def badge_nkg_ext(val): return f"🟢 {val} N/kg" if val >= 4.5 else f"🔴 {val} N/kg (Débil)"
                    def badge_nkg_flx(val): return f"🟢 {val} N/kg" if val >= 3.5 else f"🔴 {val} N/kg (Débil)"
                    
                    st.markdown("**Ratios Clínicos de Equilibrio**")
                    cr1, cr2, cr3, cr4 = st.columns(4)
                    with cr1: st.info(f"**Isquio/Cuád (D):**\n{badge_hq(ratio_hq_d)}")
                    with cr2: st.info(f"**Isquio/Cuád (I):**\n{badge_hq(ratio_hq_i)}")
                    with cr3: st.info(f"**Adu/Abd (D):**\n{badge_adab(ratio_adab_d)}")
                    with cr4: st.info(f"**Adu/Abd (I):**\n{badge_adab(ratio_adab_i)}")
    
                    st.markdown("**Fuerza Relativa Isométrica (N/kg)**")
                    cf_rel1, cf_rel2, cf_rel3, cf_rel4 = st.columns(4)
                    with cf_rel1: st.info(f"**Cuádriceps (D):**\n{badge_nkg_ext(f_rel_ext_d)}\n*(Óptimo > 4.5)*")
                    with cf_rel2: st.info(f"**Cuádriceps (I):**\n{badge_nkg_ext(f_rel_ext_i)}\n*(Óptimo > 4.5)*")
                    with cf_rel3: st.info(f"**Isquiosural (D):**\n{badge_nkg_flx(f_rel_flx_d)}\n*(Óptimo > 3.5)*")
                    with cf_rel4: st.info(f"**Isquiosural (I):**\n{badge_nkg_flx(f_rel_flx_i)}\n*(Óptimo > 3.5)*")
    
                    st.markdown("---")

                    st.markdown("#### 🏋️‍♂️ 4. Fuerza Máxima, Perfil F-V y DSI")
                    sq_rm = safe_float(v_data.get('rm_sentadilla'))
                    dl_rm = safe_float(v_data.get('rm_peso_muerto'))
                    f_rel_sq = round(sq_rm / peso_actual, 2) if peso_actual > 0 else 0
                    f_rel_dl = round(dl_rm / peso_actual, 2) if peso_actual > 0 else 0
                    
                    crm1, crm2, crm3, crm4 = st.columns(4)
                    with crm1: tarjeta_kpi("Estimación 1RM Sentadilla", f"{sq_rm} kg")
                    with crm2: tarjeta_kpi("Estimación 1RM Peso Muerto", f"{dl_rm} kg")
                    with crm3: tarjeta_kpi("Fuerza Relativa Sentadilla", f"{f_rel_sq}x Peso Corporal")
                    with crm4: tarjeta_kpi("Fuerza Relativa Peso Muerto", f"{f_rel_dl}x Peso Corporal")
                    
                    dsi_adaptado = round(cmj_bi / f_rel_sq, 1) if f_rel_sq > 0 else 0
                    if dsi_adaptado > 25: diag_dsi = "🔴 Déficit de Fuerza (Alto CMJ, base débil. Priorizar Sentadilla pesada)"
                    elif dsi_adaptado > 0 and dsi_adaptado < 18: diag_dsi = "🟡 Déficit de Potencia (Fuerte pero lento. Priorizar Pliometría/Balísticos)"
                    elif dsi_adaptado >= 18 and dsi_adaptado <= 25: diag_dsi = "🟢 Transferencia Óptima (Equilibrio Fuerza-Potencia)"
                    else: diag_dsi = "Datos insuficientes"
                        
                    st.info(f"**Índice de Fuerza Dinámica Adaptado (DSI):** {dsi_adaptado}\n\n*Diagnóstico:* {diag_dsi}")

                    def analizar_perfil_fv(datos_json, titulo, peso_corp):
                        if not datos_json or not isinstance(datos_json, dict): return None, None
                        kgs = np.array([k for k, v in zip(datos_json.get('kg', []), datos_json.get('vel', [])) if k > 0 and v > 0])
                        vels = np.array([v for k, v in zip(datos_json.get('kg', []), datos_json.get('vel', [])) if k > 0 and v > 0])
                        
                        if len(kgs) > 1:
                            z = np.polyfit(kgs, vels, 1)
                            p = np.poly1d(z)
                            slope, intercept = z[0], z[1]
                            
                            ss_res = np.sum((vels - p(kgs))**2)
                            ss_tot = np.sum((vels - np.mean(vels))**2)
                            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                            
                            v0 = intercept
                            f0_kg = -intercept / slope if slope < 0 else 0
                            f0_rel = f0_kg / peso_corp if peso_corp > 0 else 0
                            
                            if f0_rel >= 2.2 and v0 >= 1.3: cuadrante = "🟢 Perfil Óptimo (Fuerte y Rápido)"
                            elif f0_rel < 2.2 and v0 >= 1.3: cuadrante = "🟡 Déficit de Fuerza (Rápido pero Débil)"
                            elif f0_rel >= 2.2 and v0 < 1.3: cuadrante = "🟡 Déficit de Velocidad (Fuerte pero Lento)"
                            else: cuadrante = "🔴 Déficit Global (Débil y Lento)"
                                
                            fig = px.scatter(x=kgs, y=vels, labels={'x': 'Carga (kg)', 'y': 'Velocidad (m/s)'}, title=titulo)
                            fig.update_traces(marker=dict(size=10, color='#10833d'))
                            x_trend = np.linspace(min(kgs), max(kgs), 50)
                            fig.add_scatter(x=x_trend, y=p(x_trend), mode='lines', name='Tendencia', line=dict(dash='dash', color='#09274e'))
                            fig.update_layout(showlegend=False, height=300, margin=dict(l=20, r=20, t=40, b=20))
                            
                            return fig, {"r2": r2, "v0": v0, "f0_kg": f0_kg, "cuadrante": cuadrante}
                        return None, None

                    p_sq_data = v_data.get('perfil_sentadilla', {})
                    p_pm_data = v_data.get('perfil_peso_muerto', {})
                    
                    fig_sq, stats_sq = analizar_perfil_fv(p_sq_data, "Perfil F-V Sentadilla", peso_actual)
                    fig_pm, stats_pm = analizar_perfil_fv(p_pm_data, "Perfil F-V Peso Muerto", peso_actual)

                    if fig_sq or fig_pm:
                        c_fig1, c_fig2 = st.columns(2)
                        with c_fig1:
                            if fig_sq:
                                st.plotly_chart(fig_sq, use_container_width=True)
                                fiabilidad_sq = "🟢 Excelente" if stats_sq['r2'] >= 0.95 else ("🟡 Aceptable" if stats_sq['r2'] >= 0.90 else "🔴 Pobre (Falta intención)")
                                st.info(f"**Diagnóstico SQ:** {stats_sq['cuadrante']}\n\n**V0 Teórica:** {round(stats_sq['v0'], 2)} m/s | **F0 Teórica:** {round(stats_sq['f0_kg'], 1)} kg\n\n**Fiabilidad del test ($R^2$):** {round(stats_sq['r2'], 3)} ({fiabilidad_sq})")
                        with c_fig2:
                            if fig_pm:
                                st.plotly_chart(fig_pm, use_container_width=True)
                                fiabilidad_pm = "🟢 Excelente" if stats_pm['r2'] >= 0.95 else ("🟡 Aceptable" if stats_pm['r2'] >= 0.90 else "🔴 Pobre (Falta intención)")
                                st.info(f"**Diagnóstico PM:** {stats_pm['cuadrante']}\n\n**V0 Teórica:** {round(stats_pm['v0'], 2)} m/s | **F0 Teórica:** {round(stats_pm['f0_kg'], 1)} kg\n\n**Fiabilidad del test ($R^2$):** {round(stats_pm['r2'], 3)} ({fiabilidad_pm})")

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
                                "Ejercicio Accesorio": ["Empuje de Cadera", "Peso Muerto Asimétrico", "Sentadilla Búlgara", "Zancada", "PM Rumano Unilateral"],
                                "Estimación (kg)": [round(sq_rm * 1.20, 1), round(dl_rm * 0.70, 1), round(sq_rm * 0.50, 1), round(sq_rm * 0.45, 1), round(dl_rm * 0.45, 1)]
                            })
                            st.dataframe(df_acc, hide_index=True)

                    st.markdown("---")
                    
                    st.markdown("#### 🧭 5. Asimetría Direccional Global (El Eslabón Débil)")
                    puntos_der, puntos_izq, empates = 0, 0, 0
                    pruebas_uni = [
                        (v_data.get('fms_paso_obstaculo_der',0), v_data.get('fms_paso_obstaculo_izq',0)),
                        (v_data.get('fms_zancada_der',0), v_data.get('fms_zancada_izq',0)),
                        (v_data.get('fms_mov_hombro_der',0), v_data.get('fms_mov_hombro_izq',0)),
                        (v_data.get('fms_elevacion_pierna_der',0), v_data.get('fms_elevacion_pierna_izq',0)),
                        (v_data.get('cmj_uni_der',0), v_data.get('cmj_uni_izq',0)),
                        (v_data.get('salto_horiz_der',0), v_data.get('salto_horiz_izq',0)),
                        (v_data.get('iso_ext_rodilla_der',0), v_data.get('iso_ext_rodilla_izq',0)),
                        (v_data.get('iso_flex_rodilla_der',0), v_data.get('iso_flex_rodilla_izq',0)),
                        (v_data.get('iso_add_cadera_der',0), v_data.get('iso_add_cadera_izq',0)),
                        (v_data.get('iso_abd_cadera_der',0), v_data.get('iso_abd_cadera_izq',0))
                    ]
                    
                    for der, izq in pruebas_uni:
                        if safe_float(der) > safe_float(izq): puntos_der += 1
                        elif safe_float(izq) > safe_float(der): puntos_izq += 1
                        else: empates += 1
                    
                    if puntos_der >= puntos_izq + 3:
                        dom_txt = "🦵 Dominancia Derecha Consistente"
                        eslabon_txt = "⚠️ Hemicuerpo Izquierdo (Priorizar entrenamiento compensatorio)"
                    elif puntos_izq >= puntos_der + 3:
                        dom_txt = "🦵 Dominancia Izquierda Consistente"
                        eslabon_txt = "⚠️ Hemicuerpo Derecho (Priorizar entrenamiento compensatorio)"
                    else:
                        dom_txt = "⚖️ Perfil Simétrico Equilibrado"
                        eslabon_txt = "Ninguno (Buen control inter-extremidades)"
                        
                    ce1, ce2, ce3 = st.columns(3)
                    with ce1: tarjeta_kpi("Mejores Marcas (Pierna Derecha)", f"{puntos_der} / 10")
                    with ce2: tarjeta_kpi("Mejores Marcas (Pierna Izquierda)", f"{puntos_izq} / 10")
                    with ce3: tarjeta_kpi("Empates Bilaterales", f"{empates} / 10")
                    
                    st.info(f"**Análisis de Tendencia Direccional:** {dom_txt} | **Eslabón Débil a compensar:** {eslabon_txt}")

                    st.markdown("---")
                    st.markdown("#### 🎯 6. Evolución Geométrica (Radar) y Pautas Clínicas")
                    
                    col_rad1, col_rad2 = st.columns([1, 1])
                    with col_rad1:
                        st.markdown("*Perfil Físico: Inicial vs Actual*")
                        vals_cronologicas = df_temp.sort_values(by="fecha", ascending=True)
                        val_inicial_obj = vals_cronologicas.iloc[0].to_dict() if not vals_cronologicas.empty else v_data.to_dict()
                        fig_radar = generar_grafico_radar(val_inicial_obj, v_data.to_dict(), peso_actual)
                        st.plotly_chart(fig_radar, use_container_width=True)
                        
                    with col_rad2:
                        st.markdown("*Diagnóstico y Recomendaciones Automáticas*")
                        generar_recomendaciones_automaticas(v_data)

# ==========================================
# PESTAÑA 2: AÑADIR NUEVA VALORACIÓN (MANUAL O EXCEL)
# ==========================================
with tab_nuevo:
    if not jugadores:
        st.warning("Primero debes registrar deportistas en la sección de Jugadores.")
    else:
        modo_ingreso = st.radio("Método de registro:", ["📝 Formulario Manual", "📁 Importar desde Excel"], horizontal=True)
        
        # ---------------------------------------------------------
        # OPCIÓN A: FORMULARIO MANUAL
        # ---------------------------------------------------------
        if modo_ingreso == "📝 Formulario Manual":
            with st.form("form_nueva_val_detallada"):
                
                st.markdown("#### ⚙️ Datos Generales")
                cg1, cg2, cg3, cg4 = st.columns(4)
                with cg1: jugador_sel = st.selectbox("Deportista:", options=list(mapa_jugadores.keys()), format_func=lambda x: mapa_jugadores[x])
                with cg2: fecha_test = st.date_input("Fecha:", value=date.today())
                with cg3: lesion = st.radio("¿Lesión activa?", options=["No", "Sí"], horizontal=True, index=0)
                with cg4: peso = st.number_input("Peso (kg):", min_value=30.0, value=70.0, step=0.5)
                
                st.markdown("---")
                
                st.markdown("#### 🤸 1. Protocolo FMS (0 a 3)")
                cf1, cf2, cf3, cf4, cf5 = st.columns(5)
                with cf1: fms_sentadilla = st.number_input("Sentadilla (FMS 2)", 0, 3, 3)
                with cf2: fms_obstaculo_d = st.number_input("Obstáculo Der. (FMS 4)", 0, 3, 3)
                with cf3: fms_obstaculo_i = st.number_input("Obstáculo Izq. (FMS 4)", 0, 3, 3)
                with cf4: fms_zancada_d = st.number_input("Zancada Der. (FMS 5)", 0, 3, 3)
                with cf5: fms_zancada_i = st.number_input("Zancada Izq. (FMS 5)", 0, 3, 3)
                
                cf6, cf7, cf8, cf9, cf10, cf11 = st.columns(6)
                with cf6: fms_hombro_d = st.number_input("Hombro Der. (FMS 1)", 0, 3, 3)
                with cf7: fms_hombro_i = st.number_input("Hombro Izq. (FMS 1)", 0, 3, 3)
                with cf8: fms_pierna_d = st.number_input("P. Recta Der. (FMS 3)", 0, 3, 3)
                with cf9: fms_pierna_i = st.number_input("P. Recta Izq. (FMS 3)", 0, 3, 3)
                with cf10: fms_tronco = st.number_input("Est. Tronco (FMS 6)", 0, 3, 3)
                with cf11: fms_rotatoria = st.number_input("Est. Rotatoria (FMS 7)", 0, 3, 3)
    
                st.markdown("---")
                
                st.markdown("#### 🦘 2. Test de Salto (cm)")
                cs1, cs2, cs3, cs4, cs5 = st.columns(5)
                with cs1: cmj_bi = st.number_input("CMJ Bilateral", min_value=0.0, value=0.0, step=0.5)
                with cs2: cmj_ud = st.number_input("CMJ Uni. Der.", min_value=0.0, value=0.0, step=0.5)
                with cs3: cmj_ui = st.number_input("CMJ Uni. Izq.", min_value=0.0, value=0.0, step=0.5)
                with cs4: sh_d = st.number_input("Horiz. Der.", min_value=0.0, value=0.0, step=1.0)
                with cs5: sh_i = st.number_input("Horiz. Izq.", min_value=0.0, value=0.0, step=1.0)
    
                st.markdown("---")
                
                st.markdown("#### ⚡ 3. Fuerza Máxima Isométrica (N)")
                ci1, ci2, ci3, ci4 = st.columns(4)
                with ci1:
                    st.markdown("**Extensión (Cuád)**")
                    c_ed, c_ei = st.columns(2)
                    with c_ed: iso_ext_d = st.number_input("Der", min_value=0.0, value=0.0, step=1.0, key="ext_d")
                    with c_ei: iso_ext_i = st.number_input("Izq", min_value=0.0, value=0.0, step=1.0, key="ext_i")
                with ci2:
                    st.markdown("**Flexión (Isq)**")
                    c_fd, c_fi = st.columns(2)
                    with c_fd: iso_flx_d = st.number_input("Der", min_value=0.0, value=0.0, step=1.0, key="flx_d")
                    with c_fi: iso_flx_i = st.number_input("Izq", min_value=0.0, value=0.0, step=1.0, key="flx_i")
                with ci3:
                    st.markdown("**Aducción**")
                    c_ad, c_ai = st.columns(2)
                    with c_ad: iso_add_d = st.number_input("Der", min_value=0.0, value=0.0, step=1.0, key="add_d")
                    with c_ai: iso_add_i = st.number_input("Izq", min_value=0.0, value=0.0, step=1.0, key="add_i")
                with ci4:
                    st.markdown("**Abducción**")
                    c_abd, c_abi = st.columns(2)
                    with c_abd: iso_abd_d = st.number_input("Der", min_value=0.0, value=0.0, step=1.0, key="abd_d")
                    with c_abi: iso_abd_i = st.number_input("Izq", min_value=0.0, value=0.0, step=1.0, key="abd_i")
    
                st.markdown("---")
                
                st.markdown("#### 🏋️‍♂️ 4. Perfil Carga-Velocidad y 1RM")
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
                        temp_calculada = obtener_temporada(fecha_test)
                        num_val_calculado = calcular_num_valoracion(jugador_sel, temp_calculada, valoraciones)
    
                        nuevo_test = {
                            "jugador_id": jugador_sel, 
                            "fecha": str(fecha_test), 
                            "temporada": temp_calculada,
                            "numero_valoracion": num_val_calculado,
                            "lesion": lesion, "peso_corporal": float(peso),
                            "fms_sentadilla": fms_sentadilla, "fms_paso_obstaculo_der": fms_obstaculo_d, "fms_paso_obstaculo_izq": fms_obstaculo_i,
                            "fms_zancada_der": fms_zancada_d, "fms_zancada_izq": fms_zancada_i, "fms_mov_hombro_der": fms_hombro_d, "fms_mov_hombro_izq": fms_hombro_i,
                            "fms_elevacion_pierna_der": fms_pierna_d, "fms_elevacion_pierna_izq": fms_pierna_i, "fms_estabilidad_tronco": fms_tronco, "fms_estabilidad_rotatoria": fms_rotatoria,
                            "cmj_bilateral": cmj_bi, "cmj_uni_der": cmj_ud, "cmj_uni_izq": cmj_ui, "salto_horiz_der": sh_d, "salto_horiz_izq": sh_i,
                            "iso_ext_rodilla_der": iso_ext_d, "iso_ext_rodilla_izq": iso_ext_i, "iso_flex_rodilla_der": iso_flx_d, "iso_flex_rodilla_izq": iso_flx_i,
                            "iso_add_cadera_der": iso_add_d, "iso_add_cadera_izq": iso_add_i, "iso_abd_cadera_der": iso_abd_d, "iso_abd_cadera_izq": iso_abd_i,
                            "rm_sentadilla": float(rm_sq), "rm_peso_muerto": float(rm_pm),
                            "perfil_sentadilla": {"kg": p_sq, "vel": v_sq},
                            "perfil_peso_muerto": {"kg": p_pm, "vel": v_pm},
                            "comentarios": comentarios
                        }
                        supabase.table("valoraciones_condicionales").insert(nuevo_test).execute()
                        cargar_datos_sistema(force_refresh=True)
                        st.success(f"¡Valoración #{num_val_calculado} (Temporada {temp_calculada}) guardada correctamente!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")

        # ---------------------------------------------------------
        # OPCIÓN B: IMPORTACIÓN DESDE EXCEL
        # ---------------------------------------------------------
        else:
            st.markdown("#### 📁 Importación Masiva (Excel)")
            
            with st.expander("👀 Ver lista de nombres exactos registrados en la base de datos"):
                if jugadores:
                    nombres_db = sorted([j['nombre'] for j in jugadores])
                    st.dataframe(pd.DataFrame(nombres_db, columns=["Nombres válidos en el sistema"]), use_container_width=True, hide_index=True)
                else:
                    st.write("Aún no hay deportistas registrados.")
            
            # --- MAPEO ADAPTADO EXACTAMENTE A TUS COLUMNAS ---
            MAPEO = {
                "nombre": "NOMBRE", "fecha": "FECHA", "lesion": "LESIÓN", "peso": "PESO",
                "fms1_d": "FMS1. D", "fms1_nd": "FMS1. ND", "fms2": "FMS2.",
                "fms3_d": "FMS3. D", "fms3_nd": "FMS3. ND", "fms4_d": "FMS4. D", "fms4_nd": "FMS4. ND",
                "fms5_d": "FMS5. D", "fms5_nd": "FMS5. ND", "fms6": "FMS6", "fms7": "FMS7",
                "sh_d": "SH. D", "sh_nd": "SH. ND", "cmj_bi": "CMJ", "cmj_d": "CMJ D", "cmj_nd": "CMJ ND",
                "er_d": "ER D", "er_nd": "ER ND", "fr_d": "FR D", "fr_nd": "FR ND",
                "abd_d": "ABD D", "abd_nd": "ABD ND", "ad_d": "AD D", "ad_nd": "AD ND",
                "sq_kg": ["SQ KG 1", "SQ KG 2", "SQ KG 3", "SQ KG 4", "SQ KG 5"],
                "sq_v": ["SQ V 1", "SQ V 2", "SQ V 3", "SQ V 4", "SQ V 5"],
                "rdl_kg": ["RDL KG 1", "RDL KG 2", "RDL KG 3", "RDL KG 4", "RDL KG 5"],
                "rdl_v": ["RDL V 1", "RDL V 2", "RDL V 3", "RDL V 4", "RDL V 5"]
            }

            archivo = st.file_uploader("Sube tu plantilla Excel (.xlsx)", type=["xlsx", "xls"])
            
            if archivo:
                try:
                    df_import = pd.read_excel(archivo)
                    st.write("**Vista previa de los primeros registros leídos:**")
                    st.dataframe(df_import.head(3))
                    
                    if st.button("🚀 Subir e Importar Datos", type="primary", use_container_width=True):
                        registros_exitosos = 0
                        errores = []
                        
                        for idx, row in df_import.iterrows():
                            nombre_excel = str(row.get(MAPEO["nombre"], "")).strip()
                            jugador_db = next((j for j in jugadores if j['nombre'].lower() == nombre_excel.lower()), None)
                            
                            if not jugador_db:
                                errores.append(f"Fila {idx+2}: No se encontró al jugador '{nombre_excel}'.")
                                continue
                                
                            try:
                                fecha_obj = pd.to_datetime(row.get(MAPEO["fecha"])).date()
                                temp_calc = obtener_temporada(fecha_obj)
                                num_val_calc = calcular_num_valoracion(jugador_db['id'], temp_calc, valoraciones)
                                
                                # Función para sanear vacíos de excel
                                def s(val): return 0.0 if pd.isna(val) else float(val)
                                
                                # Lógica inteligente: D/ND -> Der/Izq según perfil del jugador
                                def map_d_nd(val_d, val_nd, is_brazo=False):
                                    dom = jugador_db.get('brazo_dominante' if is_brazo else 'pierna_dominante', 'Derecho' if is_brazo else 'Derecha')
                                    # Si es zurdo, invertimos el guardado en base de datos
                                    if dom in ['Izquierdo', 'Izquierda']:
                                        return {"der": s(val_nd), "izq": s(val_d)}
                                    return {"der": s(val_d), "izq": s(val_nd)}

                                # Extracción de perfiles F-V
                                p_sq = [s(row.get(col)) for col in MAPEO["sq_kg"]]
                                v_sq = [s(row.get(col)) for col in MAPEO["sq_v"]]
                                p_rdl = [s(row.get(col)) for col in MAPEO["rdl_kg"]]
                                v_rdl = [s(row.get(col)) for col in MAPEO["rdl_v"]]

                                # Cálculo de 1RM automático
                                def calcular_rm_final_import(pesos, vels):
                                    validas = [(pesos[i], vels[i]) for i in range(5) if vels[i] > 0 and pesos[i] > 0]
                                    if validas:
                                        p_max, v_max = max(validas, key=lambda x: x[0])
                                        return round(p_max / v_max, 1)
                                    return round(max(pesos), 1) if max(pesos) > 0 else 0.0
                                    
                                fms1 = map_d_nd(row.get(MAPEO["fms1_d"]), row.get(MAPEO["fms1_nd"]), is_brazo=True)
                                fms3 = map_d_nd(row.get(MAPEO["fms3_d"]), row.get(MAPEO["fms3_nd"]))
                                fms4 = map_d_nd(row.get(MAPEO["fms4_d"]), row.get(MAPEO["fms4_nd"]))
                                fms5 = map_d_nd(row.get(MAPEO["fms5_d"]), row.get(MAPEO["fms5_nd"]))
                                sh = map_d_nd(row.get(MAPEO["sh_d"]), row.get(MAPEO["sh_nd"]))
                                cmj = map_d_nd(row.get(MAPEO["cmj_d"]), row.get(MAPEO["cmj_nd"]))
                                iso_ext = map_d_nd(row.get(MAPEO["er_d"]), row.get(MAPEO["er_nd"]))
                                iso_flx = map_d_nd(row.get(MAPEO["fr_d"]), row.get(MAPEO["fr_nd"]))
                                iso_abd = map_d_nd(row.get(MAPEO["abd_d"]), row.get(MAPEO["abd_nd"]))
                                iso_add = map_d_nd(row.get(MAPEO["ad_d"]), row.get(MAPEO["ad_nd"]))

                                nuevo_test = {
                                    "jugador_id": jugador_db['id'], 
                                    "fecha": str(fecha_obj), 
                                    "temporada": temp_calc,
                                    "numero_valoracion": num_val_calc,
                                    "lesion": "Sí" if str(row.get(MAPEO["lesion"], "")).lower().strip() in ["sí", "si", "yes", "s", "1"] else "No",
                                    "peso_corporal": s(row.get(MAPEO["peso"])),
                                    # FMS
                                    "fms_mov_hombro_der": int(fms1["der"]), "fms_mov_hombro_izq": int(fms1["izq"]),
                                    "fms_sentadilla": int(s(row.get(MAPEO["fms2"]))),
                                    "fms_elevacion_pierna_der": int(fms3["der"]), "fms_elevacion_pierna_izq": int(fms3["izq"]),
                                    "fms_paso_obstaculo_der": int(fms4["der"]), "fms_paso_obstaculo_izq": int(fms4["izq"]),
                                    "fms_zancada_der": int(fms5["der"]), "fms_zancada_izq": int(fms5["izq"]),
                                    "fms_estabilidad_tronco": int(s(row.get(MAPEO["fms6"]))),
                                    "fms_estabilidad_rotatoria": int(s(row.get(MAPEO["fms7"]))),
                                    # Salto
                                    "cmj_bilateral": s(row.get(MAPEO["cmj_bi"])),
                                    "cmj_uni_der": cmj["der"], "cmj_uni_izq": cmj["izq"],
                                    "salto_horiz_der": sh["der"], "salto_horiz_izq": sh["izq"],
                                    # Isometría
                                    "iso_ext_rodilla_der": iso_ext["der"], "iso_ext_rodilla_izq": iso_ext["izq"],
                                    "iso_flex_rodilla_der": iso_flx["der"], "iso_flex_rodilla_izq": iso_flx["izq"],
                                    "iso_add_cadera_der": iso_add["der"], "iso_add_cadera_izq": iso_add["izq"],
                                    "iso_abd_cadera_der": iso_abd["der"], "iso_abd_cadera_izq": iso_abd["izq"],
                                    # RM y Perfiles (Cálculo y guardado)
                                    "rm_sentadilla": float(calcular_rm_final_import(p_sq, v_sq)),
                                    "rm_peso_muerto": float(calcular_rm_final_import(p_rdl, v_rdl)),
                                    "perfil_sentadilla": {"kg": p_sq, "vel": v_sq},
                                    "perfil_peso_muerto": {"kg": p_rdl, "vel": v_rdl},
                                    "comentarios": "Importado desde Excel."
                                }
                                
                                supabase.table("valoraciones_condicionales").insert(nuevo_test).execute()
                                valoraciones.append(nuevo_test)
                                registros_exitosos += 1
                                
                            except Exception as e_row:
                                errores.append(f"Fila {idx+2} ({nombre_excel}): Error de formato - {e_row}")
                                
                        cargar_datos_sistema(force_refresh=True)
                        if registros_exitosos > 0:
                            st.success(f"¡Se han importado {registros_exitosos} valoraciones correctamente!")
                        if errores:
                            st.error("Se encontraron errores:")
                            for err in errores: st.write(f"- {err}")
                        if registros_exitosos > 0:
                            st.rerun()
                except Exception as e:
                    st.error(f"Error general al procesar el Excel: {e}")

# ==========================================
# PESTAÑA 3: TABLA DE REGISTROS Y GESTIÓN
# ==========================================
with tab_reg:
    st.markdown("### 📋 Tabla de Registros y Gestión")
    
    if not valoraciones:
        st.info("No hay valoraciones registradas todavía.")
    else:
        from collections import Counter
        pares_jugador_fecha = [(v['jugador_id'], v['fecha']) for v in valoraciones]
        duplicados = [item for item, count in Counter(pares_jugador_fecha).items() if count > 1]
        
        if duplicados:
            st.error("⚠️ **¡Atención! Se han detectado valoraciones duplicadas (mismo deportista el mismo día).**")
            for dup in duplicados:
                nombre_dup = mapa_jugadores.get(dup[0], 'Desconocido')
                st.write(f"- {nombre_dup} tiene más de un registro el {dup[1]}")
            st.markdown("---")

        df_vals_completos = pd.DataFrame(valoraciones)
        df_vals_completos['Deportista'] = df_vals_completos['jugador_id'].map(mapa_jugadores)
        
        cf1, cf2 = st.columns(2)
        with cf1:
            lista_jugadores_unicos = sorted(df_vals_completos['Deportista'].dropna().unique())
            filtro_jug = st.selectbox("Filtrar por Deportista:", ["Todos"] + lista_jugadores_unicos)
        with cf2:
            lista_temps = sorted(df_vals_completos['temporada'].dropna().unique())
            filtro_temp = st.selectbox("Filtrar por Temporada:", ["Todas"] + lista_temps)
            
        df_filtrado = df_vals_completos.copy()
        if filtro_jug != "Todos": df_filtrado = df_filtrado[df_filtrado['Deportista'] == filtro_jug]
        if filtro_temp != "Todas": df_filtrado = df_filtrado[df_filtrado['temporada'] == filtro_temp]

        renombres = {
            'fecha': 'Fecha', 'temporada': 'Temporada', 'numero_valoracion': 'Nº Val.', 'Deportista': 'Deportista', 'lesion': 'Lesión', 'peso_corporal': 'Peso (kg)',
            'fms_sentadilla': 'FMS Sentadilla', 'fms_paso_obstaculo_der': 'FMS Paso Obst. (Der)', 'fms_paso_obstaculo_izq': 'FMS Paso Obst. (Izq)',
            'fms_zancada_der': 'FMS Zancada (Der)', 'fms_zancada_izq': 'FMS Zancada (Izq)', 'fms_mov_hombro_der': 'FMS Hombro (Der)', 'fms_mov_hombro_izq': 'FMS Hombro (Izq)', 
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
        
        cols_base = ['Deportista', 'Fecha', 'Temporada', 'Nº Val.', 'Lesión', 'Peso (kg)']
        df_mostrar = df_filtrado.rename(columns=renombres)
        cols_existentes = [c for c in df_mostrar.columns if c in renombres.values()]
        orden_final = cols_base + [c for c in cols_existentes if c not in cols_base]
        
        st.dataframe(df_mostrar[orden_final], use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### ⚙️ Gestión: Modificar o Eliminar Registro")
        opciones_gestion = {row['id']: f"{row['Deportista']} - {row['fecha']} (Val. {row['numero_valoracion']})" for idx, row in df_filtrado.iterrows()}
        
        val_seleccionada = st.selectbox("Selecciona una valoración para gestionarla:", [None] + list(opciones_gestion.keys()), format_func=lambda x: opciones_gestion[x] if x else "Seleccionar registro...")
        
        if val_seleccionada:
            val_actual = next((v for v in valoraciones if v['id'] == val_seleccionada), None)
            
            if val_actual:
                with st.form("form_editar_valoracion"):
                    st.info(f"Modificando datos de: **{mapa_jugadores.get(val_actual.get('jugador_id'), '')}**")
                    
                    st.markdown("**⚙️ Datos Básicos**")
                    # TAMBIÉN SE ELIMINARON LOS CAMPOS AQUI
                    ce1, ce2, ce3 = st.columns(3)
                    with ce1: e_fecha = st.date_input("Fecha:", value=pd.to_datetime(val_actual.get('fecha')).date())
                    with ce2: 
                        les_idx = 0 if val_actual.get('lesion') == "No" else 1
                        e_lesion = st.radio("¿Lesión activa?", ["No", "Sí"], index=les_idx, horizontal=True)
                    with ce3: 
                        peso_bd = float(val_actual.get('peso_corporal', 70.0))
                        peso_seguro = peso_bd if peso_bd >= 30.0 else 70.0
                        e_peso = st.number_input("Peso (kg):", min_value=30.0, value=peso_seguro)

                    st.markdown("**🤸 1. Protocolo FMS**")
                    cf_e1, cf_e2, cf_e3, cf_e4, cf_e5, cf_e6 = st.columns(6)
                    with cf_e1: 
                        ef_sq = st.number_input("Sentadilla", 0, 3, int(val_actual.get('fms_sentadilla', 0)))
                        ef_tronco = st.number_input("Est. Tronco", 0, 3, int(val_actual.get('fms_estabilidad_tronco', 0)))
                    with cf_e2: 
                        ef_obs_d = st.number_input("Obst. Der", 0, 3, int(val_actual.get('fms_paso_obstaculo_der', 0)))
                        ef_obs_i = st.number_input("Obst. Izq", 0, 3, int(val_actual.get('fms_paso_obstaculo_izq', 0)))
                    with cf_e3: 
                        ef_zan_d = st.number_input("Zanc. Der", 0, 3, int(val_actual.get('fms_zancada_der', 0)))
                        ef_zan_i = st.number_input("Zanc. Izq", 0, 3, int(val_actual.get('fms_zancada_izq', 0)))
                    with cf_e4:
                        ef_hom_d = st.number_input("Homb. Der", 0, 3, int(val_actual.get('fms_mov_hombro_der', 0)))
                        ef_hom_i = st.number_input("Homb. Izq", 0, 3, int(val_actual.get('fms_mov_hombro_izq', 0)))
                    with cf_e5:
                        ef_pie_d = st.number_input("Pier. Der", 0, 3, int(val_actual.get('fms_elevacion_pierna_der', 0)))
                        ef_pie_i = st.number_input("Pier. Izq", 0, 3, int(val_actual.get('fms_elevacion_pierna_izq', 0)))
                    with cf_e6:
                        ef_rot = st.number_input("Est. Rotatoria", 0, 3, int(val_actual.get('fms_estabilidad_rotatoria', 0)))

                    st.markdown("**🦘 2. Salto (cm)**")
                    cs_e1, cs_e2, cs_e3, cs_e4, cs_e5 = st.columns(5)
                    with cs_e1: e_cmj_bi = st.number_input("CMJ Bi", value=float(val_actual.get('cmj_bilateral', 0)))
                    with cs_e2: e_cmj_ud = st.number_input("CMJ Uni D", value=float(val_actual.get('cmj_uni_der', 0)))
                    with cs_e3: e_cmj_ui = st.number_input("CMJ Uni I", value=float(val_actual.get('cmj_uni_izq', 0)))
                    with cs_e4: e_sh_d = st.number_input("Horiz. D", value=float(val_actual.get('salto_horiz_der', 0)))
                    with cs_e5: e_sh_i = st.number_input("Horiz. I", value=float(val_actual.get('salto_horiz_izq', 0)))

                    st.markdown("**⚡ 3. Isometría (N)**")
                    ci_e1, ci_e2, ci_e3, ci_e4 = st.columns(4)
                    with ci_e1:
                        e_ext_d = st.number_input("Ext. Cuád D", value=float(val_actual.get('iso_ext_rodilla_der', 0)))
                        e_ext_i = st.number_input("Ext. Cuád I", value=float(val_actual.get('iso_ext_rodilla_izq', 0)))
                    with ci_e2:
                        e_flx_d = st.number_input("Flex. Isq D", value=float(val_actual.get('iso_flex_rodilla_der', 0)))
                        e_flx_i = st.number_input("Flex. Isq I", value=float(val_actual.get('iso_flex_rodilla_izq', 0)))
                    with ci_e3:
                        e_add_d = st.number_input("Aducción D", value=float(val_actual.get('iso_add_cadera_der', 0)))
                        e_add_i = st.number_input("Aducción I", value=float(val_actual.get('iso_add_cadera_izq', 0)))
                    with ci_e4:
                        e_abd_d = st.number_input("Abducción D", value=float(val_actual.get('iso_abd_cadera_der', 0)))
                        e_abd_i = st.number_input("Abducción I", value=float(val_actual.get('iso_abd_cadera_izq', 0)))

                    st.markdown("**🏋️‍♂️ 4. RM Estimado y Observaciones**")
                    cr_e1, cr_e2, cr_e3 = st.columns([1, 1, 2])
                    with cr_e1: e_rm_sq = st.number_input("1RM Sentadilla", value=float(val_actual.get('rm_sentadilla', 0)))
                    with cr_e2: e_rm_pm = st.number_input("1RM Peso Muerto", value=float(val_actual.get('rm_peso_muerto', 0)))
                    with cr_e3: e_comentarios = st.text_input("Observaciones", value=val_actual.get('comentarios', ''))

                    if st.form_submit_button("💾 Guardar Modificaciones", use_container_width=True):
                        try:
                            # =========================================================
                            # RE-CÁLCULOS AL EDITAR (por si cambió de fecha)
                            # =========================================================
                            temp_calculada = obtener_temporada(e_fecha)
                            
                            # Si mantiene la temporada, respeta su número. Si cambia a otra temporada, lo recalcula.
                            if temp_calculada == val_actual.get('temporada'):
                                num_val_calculado = val_actual.get('numero_valoracion')
                            else:
                                num_val_calculado = calcular_num_valoracion(val_actual.get('jugador_id'), temp_calculada, valoraciones, val_seleccionada)

                            datos_actualizados = {
                                "fecha": str(e_fecha), 
                                "temporada": temp_calculada,             # Automático
                                "numero_valoracion": int(num_val_calculado),  # Automático
                                "lesion": e_lesion, "peso_corporal": float(e_peso),
                                "fms_sentadilla": ef_sq, "fms_paso_obstaculo_der": ef_obs_d, "fms_paso_obstaculo_izq": ef_obs_i,
                                "fms_zancada_der": ef_zan_d, "fms_zancada_izq": ef_zan_i, "fms_mov_hombro_der": ef_hom_d, "fms_mov_hombro_izq": ef_hom_i,
                                "fms_elevacion_pierna_der": ef_pie_d, "fms_elevacion_pierna_izq": ef_pie_i, "fms_estabilidad_tronco": ef_tronco, "fms_estabilidad_rotatoria": ef_rot,
                                "cmj_bilateral": e_cmj_bi, "cmj_uni_der": e_cmj_ud, "cmj_uni_izq": e_cmj_ui, "salto_horiz_der": e_sh_d, "salto_horiz_izq": e_sh_i,
                                "iso_ext_rodilla_der": e_ext_d, "iso_ext_rodilla_izq": e_ext_i, "iso_flex_rodilla_der": e_flx_d, "iso_flex_rodilla_izq": e_flx_i,
                                "iso_add_cadera_der": e_add_d, "iso_add_cadera_izq": e_add_i, "iso_abd_cadera_der": e_abd_d, "iso_abd_cadera_izq": e_abd_i,
                                "rm_sentadilla": float(e_rm_sq), "rm_peso_muerto": float(e_rm_pm), "comentarios": e_comentarios
                            }
                            supabase.table("valoraciones_condicionales").update(datos_actualizados).eq("id", val_seleccionada).execute()
                            from database.db_manager import cargar_datos_sistema
                            cargar_datos_sistema(force_refresh=True)
                            st.success("¡Registro actualizado correctamente!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al actualizar: {e}")
                            
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Eliminar Registro Definitivamente", type="primary", use_container_width=True):
                    try:
                        supabase.table("valoraciones_condicionales").delete().eq("id", val_seleccionada).execute()
                        from database.db_manager import cargar_datos_sistema
                        cargar_datos_sistema(force_refresh=True)
                        st.success("¡Registro eliminado correctamente!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al eliminar: {e}")
