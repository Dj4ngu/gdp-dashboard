import streamlit as st
import pandas as pd
import math
import random
import altair as alt
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
import base64
import PyPDF2

#streamlit run c:/Projetos-API/StreamLit/gdp-dashboard/streamlit_app.py

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='GDP dashboard',
    page_icon=':earth_americas:', # This is an emoji shortcode. Could be a URL too.
)

# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data
def get_gdp_data():
    """Grab GDP data from a CSV file.

    This uses caching to avoid having to read the file every time. If we were
    reading from an HTTP endpoint instead of a file, it's a good idea to set
    a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
    """

    # Instead of a CSV on disk, you could read from an HTTP endpoint here too.
    DATA_FILENAME = Path(__file__).parent/'data/gdp_data.csv'
    raw_gdp_df = pd.read_csv(DATA_FILENAME)

    MIN_YEAR = 1960
    MAX_YEAR = 2022

    # The data above has columns like:
    # - Country Name
    # - Country Code
    # - [Stuff I don't care about]
    # - GDP for 1960
    # - GDP for 1961
    # - GDP for 1962
    # - ...
    # - GDP for 2022
    #
    # ...but I want this instead:
    # - Country Name
    # - Country Code
    # - Year
    # - GDP
    #
    # So let's pivot all those year-columns into two: Year and GDP
    gdp_df = raw_gdp_df.melt(
        ['Country Code'],
        [str(x) for x in range(MIN_YEAR, MAX_YEAR + 1)],
        'Year',
        'GDP',
    )

    # Convert years from string to integers
    gdp_df['Year'] = pd.to_numeric(gdp_df['Year'])

    return gdp_df

gdp_df = get_gdp_data()

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
'''
# :earth_americas: Painel do PIB

Explore os dados do PIB do site [World Bank Open Data](https://data.worldbank.org/). Como você
notará, os dados vão apenas até 2022 no momento, e pontos de dados para certos anos frequentemente
estão ausentes. Mas, fora isso, é uma ótima (e mencionei que é _gratuita_?) fonte de dados.
'''

# Add some spacing
''
''

min_value = gdp_df['Year'].min()
max_value = gdp_df['Year'].max()

from_year, to_year = st.slider(
    'Which years are you interested in?',
    min_value=min_value,
    max_value=max_value,
    value=[min_value, max_value])

countries = gdp_df['Country Code'].unique()

if not len(countries):
    st.warning("Select at least one country")

selected_countries = st.multiselect(
    'Which countries would you like to view?',
    countries,
    ['DEU', 'FRA', 'GBR', 'BRA', 'MEX', 'JPN'])

''
''
''

# Filter the data
filtered_gdp_df = gdp_df[
    (gdp_df['Country Code'].isin(selected_countries))
    & (gdp_df['Year'] <= to_year)
    & (from_year <= gdp_df['Year'])
]

st.header('GDP over time', divider='gray')

''

st.line_chart(
    filtered_gdp_df,
    x='Year',
    y='GDP',
    color='Country Code',
)

# Adicionar um gráfico de barras com cores aleatórias
bar_data = filtered_gdp_df.groupby('Country Code', as_index=False)['GDP'].sum()

# Gerar cores aleatórias para cada país
bar_data['color'] = [
    f'#{random.randint(0, 0xFFFFFF):06x}' for _ in range(len(bar_data))
]

bar_chart = alt.Chart(bar_data).mark_bar().encode(
    x=alt.X('Country Code:N', title='Country Code'),
    y=alt.Y('GDP:Q', title='Total GDP'),
    color=alt.Color('color:N', scale=None, legend=None)  # Usar cores aleatórias
).properties(
    width=700,
    height=400
)

st.altair_chart(bar_chart, use_container_width=True)

''
''


first_year = gdp_df[gdp_df['Year'] == from_year]
last_year = gdp_df[gdp_df['Year'] == to_year]

st.header(f'GDP in {to_year}', divider='gray')

''

cols = st.columns(4)

for i, country in enumerate(selected_countries):
    col = cols[i % len(cols)]

    with col:
        first_gdp = first_year[first_year['Country Code'] == country]['GDP'].iat[0] / 1000000000
        last_gdp = last_year[last_year['Country Code'] == country]['GDP'].iat[0] / 1000000000

        if math.isnan(first_gdp):
            growth = 'n/a'
            delta_color = 'off'
        else:
            growth = f'{last_gdp / first_gdp:,.2f}x'
            delta_color = 'normal'

        st.metric(
            label=f'{country} GDP',
            value=f'{last_gdp:,.0f}B',
            delta=growth,
            delta_color=delta_color
        )


# # Adicionar um botão para carregar arquivos
# st.header("Carregar Arquivos", divider="gray")

# uploaded_files = st.file_uploader(
#     "Selecione os arquivos",
#     type=None,  # Permite qualquer tipo de arquivo
#     accept_multiple_files=True  # Permite múltiplos arquivos
# )

# if uploaded_files:
#     st.write("Arquivos carregados:")
#     for uploaded_file in uploaded_files:
#         st.write(f"- {uploaded_file.name}")
# else:
#     st.info("Nenhum arquivo foi carregado.")

    # Adicionar um quadro para carregar e visualizar arquivos PDF
st.header("Visualizar Arquivo PDF", divider="gray")

uploaded_pdf = st.file_uploader(
    "Carregue um arquivo PDF",
    type=["pdf"],  # Restringe o upload apenas para arquivos PDF
    accept_multiple_files=False  # Apenas um arquivo por vez
)

if uploaded_pdf:
    # Exibir o nome do arquivo carregado
    st.write(f"Arquivo carregado: {uploaded_pdf.name}")

    # Ler o conteúdo do PDF
    try:
        pdf_reader = PyPDF2.PdfReader(uploaded_pdf)
        num_pages = len(pdf_reader.pages)
        st.write(f"O PDF contém {num_pages} página(s).")

        # Exibir o conteúdo da primeira página como texto
        first_page = pdf_reader.pages[0]
        st.text_area("Conteúdo da primeira página:", first_page.extract_text(), height=300)

        # Exibir o PDF diretamente na interface
        base64_pdf = base64.b64encode(uploaded_pdf.read()).decode("utf-8")
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="500" type="application/pdf"></iframe>'
        st.components.v1.html(pdf_display, height=500)
        
    except Exception as e:
        st.error(f"Erro ao processar o arquivo PDF: {e}")
else:
    st.info("Nenhum arquivo PDF foi carregado.")