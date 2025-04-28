# ======================================
# INTER3.PY FINAL - ANÁLISIS DE LLUVIA
# PARA ENTREGA UNIVERSIDAD ✅
# ======================================

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pyreadstat
import io
import tempfile

st.set_page_config(page_title="Análisis de Eventos de Lluvia", layout="wide")

st.title("Aplicación de Análisis de Lluvia")

uploaded_file = st.file_uploader("Sube tu archivo .sav de precipitaciones", type=["sav"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_file_path = tmp_file.name

    df, meta = pyreadstat.read_sav(tmp_file_path)
    df = df.rename(columns={'valor': 'Precipitacion', 'fecha': 'Fecha'})

    if 'Precipitacion' not in df.columns:
        st.error("La columna 'Precipitacion' no existe en el archivo. Verifica el archivo subido.")
        st.stop()

    fecha_inicio = pd.to_datetime('2000-01-01 00:00:00')
    df['Fecha_Correcta'] = fecha_inicio + pd.to_timedelta(np.arange(len(df)) * 5, unit='min')

    st.subheader("Datos cargados")
    st.dataframe(df[['Fecha_Correcta', 'Precipitacion']])

    threshold = 0
    intervalo = 5

    eventos = []
    evento_actual = []

    for i in range(len(df)):
        if df.loc[i, 'Precipitacion'] > threshold:
            evento_actual.append(df.loc[i])
        else:
            if evento_actual:
                eventos.append(pd.DataFrame(evento_actual))
                evento_actual = []

    if evento_actual:
        eventos.append(pd.DataFrame(evento_actual))

    tabla_eventos = []

    for evento in eventos:
        inicio = evento['Fecha_Correcta'].iloc[0]
        fin = evento['Fecha_Correcta'].iloc[-1]
        duracion_min = len(evento) * intervalo
        ptotal = evento['Precipitacion'].sum()
        idx_max = evento['Precipitacion'].idxmax()
        fecha_max = evento.loc[idx_max, 'Fecha_Correcta']
        p_max = evento.loc[idx_max, 'Precipitacion']

        if duracion_min < 30:
            categoria = '<30 min'
        elif 30 < duracion_min <= 60:
            categoria = '30-60 min'
        elif 60 < duracion_min <= 120:
            categoria = '60-120 min'
        elif 120 < duracion_min <= 180:
            categoria = '120-180 min'
        else:
            categoria = '>180 min'

        tabla_eventos.append({
            'Categoria': categoria,
            'Inicio': inicio,
            'Fin': fin,
            'Duracion (min)': duracion_min,
            'Precipitacion Total': ptotal,
            'Fecha Maxima Precipitacion': fecha_max,
            'Precipitacion Maxima': p_max
        })

    df_eventos = pd.DataFrame(tabla_eventos)

    st.subheader("Tabla de Eventos Detectados")
    st.dataframe(df_eventos)

    conteo_categorias = df_eventos['Categoria'].value_counts().reset_index()
    conteo_categorias.columns = ['Categoria', 'Cantidad de Eventos']

    st.subheader("Conteo de Eventos por Categoría")
    st.dataframe(conteo_categorias)

    categorias = ['<30 min', '30-60 min', '60-120 min', '120-180 min']

    colores_categorias = {
        '<30 min': 'blue',
        '30-60 min': 'green',
        '60-120 min': 'orange',
        '120-180 min': 'red'
    }

    st.subheader("Hietogramas por Categoría")
    for cat in categorias:
        st.markdown(f"### Categoría: {cat}")
        fig, ax = plt.subplots(figsize=(10, 4))
        for evento in eventos:
            duracion = len(evento) * intervalo
            if (
                (cat == '<30 min' and duracion < 30) or
                (cat == '30-60 min' and 30 < duracion <= 60) or
                (cat == '60-120 min' and 60 < duracion <= 120) or
                (cat == '120-180 min' and 120 < duracion <= 180)
            ):
                tiempo = evento['Fecha_Correcta']
                ax.bar(tiempo, evento['Precipitacion'].values,
                       width=pd.Timedelta(minutes=5),
                       align='center',
                       alpha=0.7,
                       color=colores_categorias[cat],
                       edgecolor='black')
        ax.set_xlabel('Fecha y Hora')
        ax.set_ylabel('Precipitación (mm)')
        ax.grid()
        st.pyplot(fig)

    st.subheader("Hietograma de Todos los Eventos")
    fig, ax = plt.subplots(figsize=(12, 4))
    for evento in eventos:
        tiempo = evento['Fecha_Correcta']
        ax.bar(tiempo, evento['Precipitacion'].values,
               width=pd.Timedelta(minutes=5),
               align='center',
               alpha=0.5,
               color='gray',
               edgecolor='black')
    ax.set_xlabel('Fecha y Hora')
    ax.set_ylabel('Precipitación (mm)')
    ax.grid()
    st.pyplot(fig)

    todas_curvas = []

    st.subheader("Eventos Normalizados por Categoría")
    for cat in categorias:
        st.markdown(f"## Categoría: {cat}")
        curvas_cat = []
        fig, ax = plt.subplots(figsize=(8, 5))
        for evento in eventos:
            duracion = len(evento) * intervalo
            if (
                (cat == '<30 min' and duracion < 30) or
                (cat == '30-60 min' and 30 < duracion <= 60) or
                (cat == '60-120 min' and 60 < duracion <= 120) or
                (cat == '120-180 min' and 120 < duracion <= 180)
            ):
                ptotal = evento['Precipitacion'].sum()
                tiempo_norm = np.linspace(0, 1, len(evento))
                lluvia_norm = evento['Precipitacion'].cumsum()/ptotal
                curva_interpolada = np.interp(np.linspace(0, 1, 100), tiempo_norm, lluvia_norm)
                curvas_cat.append(curva_interpolada)
                todas_curvas.append(curva_interpolada)
                ax.plot(tiempo_norm, lluvia_norm, alpha=0.5, color=colores_categorias[cat])

        if curvas_cat:
            promedio_cat = np.nanmean(curvas_cat, axis=0)
            t_norm = np.linspace(0, 1, 100)
            coef_cat = np.polyfit(t_norm, promedio_cat, 2)
            polinomio_cat = np.poly1d(coef_cat)
            ax.plot(t_norm, polinomio_cat(t_norm), label="Curva Ajuste", color='black')
            ax.set_xlabel('Tiempo Normalizado')
            ax.set_ylabel('Precipitación Acumulada Normalizada')
            ax.grid()
            ax.legend()
            st.pyplot(fig)

            st.subheader(f"Ecuación del Patrón para {cat}")
            st.latex(f"P^*(t) = {coef_cat[0]:.4f} t^2 + {coef_cat[1]:.4f} t + {coef_cat[2]:.4f}")

    st.subheader("Patrón Sintético Promedio de Todos los Eventos")
    t_norm = np.linspace(0, 1, 100)
    promedio_general = np.nanmean(todas_curvas, axis=0)
    coef_gen = np.polyfit(t_norm, promedio_general, 2)
    polinomio = np.poly1d(coef_gen)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(t_norm, promedio_general, label="Promedio de eventos", color='gray')
    ax.plot(t_norm, polinomio(t_norm), label="Ajuste polinomial", color='red')
    ax.set_xlabel('Tiempo Normalizado')
    ax.set_ylabel('Precipitación Acumulada Normalizada')
    ax.grid()
    ax.legend()
    st.pyplot(fig)

    st.subheader("Ecuación del Patrón Promedio General")
    st.latex(f"P^*(t) = {coef_gen[0]:.4f} t^2 + {coef_gen[1]:.4f} t + {coef_gen[2]:.4f}")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_eventos.to_excel(writer, sheet_name='Eventos', index=False)
        for categoria, df_categoria in df_eventos.groupby('Categoria'):
            df_categoria.to_excel(writer, sheet_name=categoria.replace(' ', '_')[:31], index=False)

    output.seek(0)

    st.download_button(
        label="Descargar Eventos en Excel",
        data=output,
        file_name='eventos_detectados.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
