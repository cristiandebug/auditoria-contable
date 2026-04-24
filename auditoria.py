import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Auditoría de Horas Extras", layout="wide")

st.title("🕵️‍♂️ Control de Horas Extras (Legajos > 30hs)")
st.write("Filtro automático basado en columnas E (Legajo), G (Concepto) y J (Cantidad).")

# --- BARRA LATERAL ---
st.sidebar.header("Configuración")
limite_horas = st.sidebar.number_input("Filtrar legajos con más de:", value=30)
codigos_interes = [1210, 1220]

# --- CARGA DE ARCHIVO ---
archivo_subido = st.file_uploader("Cargá el reporte de sueldos (Excel)", type=['xlsx'])

if archivo_subido:
    try:
        # Leemos el Excel
        # header=0 indica que la fila 1 son los títulos
        df = pd.read_excel(archivo_subido, header=0)
        
        # Filtramos solo las columnas que nos interesan por su índice de posición
        # E=4, G=6, J=9
        df_relevante = df.iloc[:, [4, 6, 9]].copy()
        
        # Renombramos temporalmente para trabajar fácil en el código
        df_relevante.columns = ['Legajo', 'Codigo', 'Cantidad']
        
        # Convertimos a números por si hay errores de formato en el Excel
        df_relevante['Codigo'] = pd.to_numeric(df_relevante['Codigo'], errors='coerce')
        df_relevante['Cantidad'] = pd.to_numeric(df_relevante['Cantidad'], errors='coerce')
        
        # 1. Filtramos por los códigos 1210 y 1220
        df_filtrado = df_relevante[df_relevante['Codigo'].isin(codigos_interes)]
        
        # 2. Agrupamos por Legajo (por si un empleado tiene ambos códigos)
        resumen = df_filtrado.groupby('Legajo')['Cantidad'].sum().reset_index()
        
        # 3. Aplicamos el filtro de las 30 horas (o el que pongas en la barra lateral)
        excesos = resumen[resumen['Cantidad'] > limite_horas]
        
        if not excesos.empty:
            st.success(f"Se encontraron {len(excesos)} casos de exceso.")
            
            # Ordenar de mayor a menor para que lo más crítico esté arriba
            excesos = excesos.sort_values(by='Cantidad', ascending=False)
            
            # Mostrar en la App
            st.dataframe(excesos, use_container_width=True)
            
            # Preparar la descarga
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                excesos.to_excel(writer, index=False, sheet_name='Excesos')
            
            st.download_button(
                label="📥 Descargar Excel de Excesos",
                data=buffer.getvalue(),
                file_name="auditoria_horas_extras.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info(f"No se detectaron legajos con más de {limite_horas} horas extras.")

    except Exception as e:
        st.error(f"Error técnico: {e}")
        st.warning("Asegurate de que el Excel no tenga filas combinadas en los encabezados.")