import streamlit as st
import pandas as pd
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Analizador de Eficacia RRHH", layout="wide")
HISTORIAL_FILE = "historial_completo_rrhh.csv"

def cargar_historial():
    if os.path.exists(HISTORIAL_FILE):
        return pd.read_csv(HISTORIAL_FILE)
    return pd.DataFrame(columns=["Periodo", "Total_Bajas", "Tasa_Rotacion", "Baja_Critica_Porcentaje"])

def guardar_mes(data):
    historial = cargar_historial()
    historial = pd.concat([historial[historial["Periodo"] != data["Periodo"]], 
                          pd.DataFrame([data])], ignore_index=True)
    historial.to_csv(HISTORIAL_FILE, index=False)

# --- SIDEBAR ---
st.sidebar.header("⚙️ Configuración")
mes = st.sidebar.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
anio = st.sidebar.number_input("Año", min_value=2024, max_value=2030, value=2026)
dotacion_inicial = st.sidebar.number_input("Dotación Inicial", min_value=1, value=100)
periodo_actual = f"{mes} {anio}"

st.title("📊 Análisis de Eficacia en Gestión de Personal")

archivo = st.file_uploader("Subí el Excel", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo)
    df.columns = ['Legajo', 'Sindicato', 'Ingreso', 'Egreso', 'Motivo']
    df['Ingreso'] = pd.to_datetime(df['Ingreso'])
    df['Egreso'] = pd.to_datetime(df['Egreso'])
    df['Meses_Antig'] = ((df['Egreso'] - df['Ingreso']).dt.days / 30).round(1)

    # 1. Crear Tramos de Antigüedad para el análisis de eficacia
    bins = [0, 3, 6, 12, 1200] # de 0-3m, 3-6m, 6-12m, y más de 12m
    labels = ['0-3 Meses', '3-6 Meses', '6-12 Meses', '+1 Año']
    df['Tramo_Antiguedad'] = pd.cut(df['Meses_Antig'], bins=bins, labels=labels, include_lowest=True)

    # 2. Cálculos de Porcentajes por Tramo
    conteo_tramos = df['Tramo_Antiguedad'].value_counts(normalize=True) * 100
    conteo_tramos = conteo_tramos.reindex(labels) # Ordenar cronológicamente

    total_bajas = len(df)
    tasa_rotacion = (total_bajas / dotacion_inicial) * 100

    tab1, tab2 = st.tabs(["📉 Informe de Eficacia", "📊 Datos Históricos"])

    with tab1:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Bajas", total_bajas)
        c2.metric("Tasa Rotación", f"{tasa_rotacion:.1f}%")
        
        # Identificar el tramo más crítico
        tramo_critico = conteo_tramos.idxmax()
        porcentaje_critico = conteo_tramos.max()
        c3.metric("Fuga Principal", tramo_critico, f"{porcentaje_critico:.0f}% de las bajas")

        st.markdown("---")
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.write("### Concentración de Bajas por Antigüedad")
            st.bar_chart(conteo_tramos)
            st.info(f"💡 El **{porcentaje_critico:.1f}%** de las bajas ocurren en el tramo de **{tramo_critico}**.")

        with col_g2:
            st.write("### Resumen Analítico")
            tabla_resumen = pd.DataFrame({
                "Tramo": labels,
                "Cant. Bajas": df['Tramo_Antiguedad'].value_counts().reindex(labels).values,
                "Porcentaje (%)": conteo_tramos.values
            })
            st.table(tabla_resumen)

        if st.button("💾 Guardar y Comparar con Meses Anteriores"):
            guardar_mes({
                "Periodo": periodo_actual,
                "Total_Bajas": total_bajas,
                "Tasa_Rotacion": round(tasa_rotacion, 2),
                "Baja_Critica_Porcentaje": round(porcentaje_critico, 2)
            })
            st.success("Análisis guardado exitosamente.")

    with tab2:
        hist = cargar_historial()
        if not hist.empty:
            st.write("### Evolución de la Tasa de Rotación vs. Bajas Prematuras")
            st.line_chart(hist.set_index("Periodo")[["Tasa_Rotacion", "Baja_Critica_Porcentaje"]])
            st.dataframe(hist)
else:
    st.warning("Cargá el archivo para ver el análisis de eficacia.")