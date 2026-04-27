import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Reporte Impacto Tecnológico - Cliente", page_icon="🚜", layout="wide")

# --- 2. LOGOS SUPERIORES ---
col_logo_izq, col_espacio, col_logo_der = st.columns([1, 4, 1])
with col_logo_izq:
    st.image("CSC.png", width=150)
with col_logo_der:
    st.image("JD.png", width=170)

# --- SIDEBAR: CONFIGURACIÓN ---
st.sidebar.header("⚙️ Configuración del Reporte")
archivo_subido = st.sidebar.file_uploader("Subir Excel de Cosecha", type=["xlsx", "csv"])
# Cambiado a "Bloque" según tu pedido
bloque_input = st.sidebar.text_input("Bloque", placeholder="Ej: Bloque El Timbo")

umbral_has = st.sidebar.number_input("Filtrar labores menores a (Has):", min_value=0.0, value=2.0, step=0.5)

df_final = pd.DataFrame()

if archivo_subido is not None:
    try:
        df = pd.read_csv(archivo_subido) if archivo_subido.name.endswith('.csv') else pd.read_excel(archivo_subido)
        df.columns = df.columns.str.strip()
        df_base = df[df['Superficie cosechada'] >= umbral_has].copy()

        with st.sidebar.expander("📍 Filtros de Segmentación", expanded=False):
            c_sel = st.multiselect("Cliente:", options=sorted(df_base['Clientes'].unique()),
                                   default=sorted(df_base['Clientes'].unique()))
            df_c = df_base[df_base['Clientes'].isin(c_sel)]
            g_sel = st.multiselect("Granja:", options=sorted(df_c['Granjas'].unique()),
                                   default=sorted(df_c['Granjas'].unique()))
            df_g = df_c[df_c['Granjas'].isin(g_sel)]
            ca_sel = st.multiselect("Campo:", options=sorted(df_g['Campos'].unique()),
                                    default=sorted(df_g['Campos'].unique()))
            df_ca = df_g[df_g['Campos'].isin(ca_sel)]
            cu_sel = st.multiselect("Cultivo:", options=sorted(df_ca['Tipo de cultivo'].unique()),
                                    default=sorted(df_ca['Tipo de cultivo'].unique()))

        df_final = df_ca[df_ca['Tipo de cultivo'].isin(cu_sel)].copy()
        df_final['Primera cosecha'] = pd.to_datetime(df_final['Primera cosecha'])
        df_final['Último cosechado'] = pd.to_datetime(df_final['Último cosechado'])
    except Exception as e:
        st.sidebar.error(f"Error al procesar archivo: {e}")

st.sidebar.divider()
st.sidebar.subheader("⛽ Parámetros de Combustible")
precio_gasoil = st.sidebar.number_input("Precio Gasoil (USD/L)", value=1.0)
ah_hs_l_ha = st.sidebar.number_input("Ahorro HarvestSmart (L/ha)", value=0.6)
ah_pgsa_l_ha = st.sidebar.number_input("Ahorro PGSA (L/ha)", value=0.5)

st.sidebar.subheader("🌾 Parámetros de Grano")
precio_grano_usd = st.sidebar.number_input("Precio Grano (USD/tn)", value=300.0)

c_am, c_psa = st.sidebar.columns(2)
with c_am:
    st.caption("**AutoMaintain**")
    p_sin_am = st.number_input("Sin AM (kg/ha)", value=100.0)
    p_con_am = st.number_input("Con AM (kg/ha)", value=80.0)
with c_psa:
    st.caption("**PSA**")
    p_sin_psa = st.number_input("Sin PSA (kg/ha)", value=100.0)
    p_con_psa = st.number_input("Con PSA (kg/ha)", value=90.0)

st.sidebar.subheader("✨ Calidad (BCR)")
with st.sidebar.expander("Configurar Rotos e Impurezas"):
    st.write("**AutoMaintain**")
    r_am_s = st.number_input("% Rotos s/AM", value=2.0)
    r_am_c = st.number_input("% Rotos c/AM", value=1.0)
    i_am_s = st.number_input("% Imp. s/AM", value=1.5)
    i_am_c = st.number_input("% Imp. c/AM", value=0.5)
    st.divider()
    st.write("**PSA**")
    r_psa_s = st.number_input("% Rotos s/PSA", value=2.0)
    r_psa_c = st.number_input("% Rotos c/PSA", value=1.5)
    i_psa_s = st.number_input("% Imp. s/PSA", value=1.5)
    i_psa_c = st.number_input("% Imp. c/PSA", value=1.0)

castigo_am = st.sidebar.number_input("% Castigo sin AM", value=1.5) / 100
castigo_psa = st.sidebar.number_input("% Castigo sin PSA", value=1.0) / 100


# --- CUERPO DEL INFORME ---
if archivo_subido is not None and not df_final.empty:
    st.title("🚜 Auditoría de Tecnología en Cosechadoras")
    st.subheader(f"Análisis para: {bloque_input if bloque_input else 'Flota Seleccionada'}")

    total_has_segmento = df_final['Superficie cosechada'].sum()
    total_comb = df_final['Combustible total'].sum()
    c_prom = total_comb / total_has_segmento if total_has_segmento > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Inicio", df_final['Primera cosecha'].min().strftime('%d/%m/%Y'))
    c2.metric("Fin", df_final['Último cosechado'].max().strftime('%d/%m/%Y'))
    c3.metric("Total Hectáreas", f"{total_has_segmento:,.1f} Has")
    c4.metric("Consumo Total", f"{total_comb:,.0f} Lts")
    c5.metric("Promedio L/Ha", f"{c_prom:.2f}")

    st.divider()
    st.subheader("🌾 Rendimientos Promedio por Cultivo")
    cultivos_en_data = sorted(list(df_final['Tipo de cultivo'].unique()))
    rtos_cols = st.columns(len(cultivos_en_data))
    dict_rtos = {cult: df_final[df_final['Tipo de cultivo'] == cult]['Peso húmedo'].mean() for cult in cultivos_en_data}
    for i, cult in enumerate(cultivos_en_data):
        rtos_cols[i].metric(f"Rto {cult}", f"{dict_rtos[cult]:.2f} tn/ha")

    st.divider()
    st.subheader("🛠️ Auditoría de Uso e Impacto Económico")
    maquinas_sel = st.multiselect("Seleccionar máquinas para el análisis:",
                                  options=sorted(list(df_final['Nombre de máquina'].unique())),
                                  default=sorted(list(df_final['Nombre de máquina'].unique())))

    if maquinas_sel:
        df_maquinas = df_final[df_final['Nombre de máquina'].isin(maquinas_sel)]
        total_has_maquinas = df_maquinas['Superficie cosechada'].sum()

        t_ahorro_c = 0.0; t_ahorro_g = 0.0; t_oculto = 0.0
        tecs_av = set(); tecs_aj = set()

        h1, h2, h3, h4, h5, h6 = st.columns([1.5, 1, 1.5, 1, 1.5, 1])
        h1.caption("**Máquina**"); h2.caption("**Has**"); h3.caption("**Tec. Avance**")
        h4.caption("**% Uso**"); h5.caption("**Tec. Ajuste**"); h6.caption("**% Uso**")

        for maq in maquinas_sel:
            df_m = df_maquinas[df_maquinas['Nombre de máquina'] == maq]
            h_m = df_m['Superficie cosechada'].sum()
            cult_p = df_m.groupby('Tipo de cultivo')['Superficie cosechada'].sum().idxmax()
            rto_ref = dict_rtos[cult_p]

            r1, r2, r3, r4, r5, r6 = st.columns([1.5, 1, 1.5, 1, 1.5, 1])
            r1.write(f"**{maq}**")
            r2.write(f"{h_m:,.1f}")
            t1 = r3.selectbox(f"T1_{maq}", ["HarvestSmart", "PGSA", "Sin Tecnología"], key=f"t1_{maq}",
                              label_visibility="collapsed")
            u1 = r4.number_input(f"U1_{maq}", 0, 100, 0, step=5, key=f"u1_{maq}", label_visibility="collapsed")
            t2 = r5.selectbox(f"T2_{maq}", ["AutoMaintain", "PSA", "Sin Tecnología"], key=f"t2_{maq}",
                              label_visibility="collapsed")
            u2 = r6.number_input(f"U2_{maq}", 0, 100, 0, step=5, key=f"u2_{maq}", label_visibility="collapsed")

            if t1 != "Sin Tecnología" and u1 > 0: tecs_av.add(t1)
            if t2 != "Sin Tecnología" and u2 > 0: tecs_aj.add(t2)

            v_c = (ah_hs_l_ha if t1 == "HarvestSmart" else (ah_pgsa_l_ha if t1 == "PGSA" else 0)) * precio_gasoil
            v_g = 0
            if t2 == "AutoMaintain":
                v_g = (((p_sin_am - p_con_am) / 1000) * precio_grano_usd) + (precio_grano_usd * rto_ref * castigo_am)
            elif t2 == "PSA":
                v_g = (((p_sin_psa - p_con_psa) / 1000) * precio_grano_usd) + (precio_grano_usd * rto_ref * castigo_psa)

            t_ahorro_c += (h_m * (u1 / 100) * v_c)
            t_ahorro_g += (h_m * (u2 / 100) * v_g)
            t_oculto += (h_m * (1 - u1 / 100) * v_c) + (h_m * (1 - u2 / 100) * v_g)

        st.markdown("---")
        col_res, col_param, col_pie = st.columns([1, 1, 1])
        with col_res:
            st.write("##### 💰 Resultado Económico Actual")
            ah_total = t_ahorro_c + t_ahorro_g
            pot_t = ah_total + t_oculto
            st.markdown(f"<h3 style='color: #28a745; margin-bottom: 0;'>USD {ah_total:,.0f}</h3>",
                        unsafe_allow_html=True)
            st.caption(f"Ahorro Real")
            st.markdown(f"<h3 style='color: #dc3545; margin-bottom: 0;'>USD {t_oculto:,.0f}</h3>",
                        unsafe_allow_html=True)
            st.caption("Costo Oculto")
            st.markdown(f"<h3 style='color: #007bff; margin-bottom: 0;'>USD {pot_t:,.0f}</h3>", unsafe_allow_html=True)
            st.caption("Potencial Total")
            efic = (ah_total / pot_t * 100) if pot_t > 0 else 0
            st.write(f"**Eficiencia: {efic:.1f}%**")
            st.progress(efic / 100)

        with col_param:
            st.write("##### 📝 Detalle de Tecnologías y Calidad")
            if "HarvestSmart" in tecs_av: st.write(f"🚜 **HarvestSmart:** -{ah_hs_l_ha} L/ha")
            if "PGSA" in tecs_av: st.write(f"🚜 **PGSA:** -{ah_pgsa_l_ha} L/ha")
            if "AutoMaintain" in tecs_aj:
                st.write(f"✅ **AutoMaintain:** -{p_sin_am - p_con_am:.0f} kg/ha")
                st.caption(f"Rotos: {r_am_s}% → {r_am_c}% | Imp: {i_am_s}% → {i_am_c}%")
            if "PSA" in tecs_aj:
                st.write(f"✅ **PSA:** -{p_sin_psa - p_con_psa:.0f} kg/ha")
                st.caption(f"Rotos: {r_psa_s}% → {r_psa_c}% | Imp: {i_psa_s}% → {i_psa_c}%")

        with col_pie:
            fig_pie = px.pie(values=[t_ahorro_c, t_ahorro_g, t_oculto], names=['Combustible', 'Granos', 'Costo Oculto'],
                             color_discrete_sequence=['#2ca02c', '#ff7f0e', '#dc3545'], hole=0.4)
            fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=230)
            st.plotly_chart(fig_pie, use_container_width=True)

    with st.expander("📂 Ver registros detallados"):
        st.dataframe(df_final, use_container_width=True)
else:
    st.info("👋 Por favor, carga el archivo de cosecha para iniciar la auditoría.")