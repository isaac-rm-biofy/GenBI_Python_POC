import streamlit as st
import time
import matplotlib.pyplot as plt
import seaborn as sns

from askPostgres import (
    ask_oci_genai,
    panda_table_from_query,
    plot_code_from_genai,
    ask_postgres,
)
from askPostgres import DB_MIGRATION, DB_SPOTIFY


def display_table(df):
    """Exibe um DataFrame pandas como uma tabela no Streamlit."""
    st.write(df)


def display_plot_code(code):
    """Exibe o código para plotagem em um bloco de código no Streamlit."""
    st.code(code, language='python')


# Configurando a barra lateral
st.sidebar.title("Histórico de Perguntas")
history = st.sidebar.empty()


if "questions_history" not in st.session_state:
    st.session_state.questions_history = []

st.title('ChatDB - Interacting with a GenAI Database')

st.write('### Ask:')
ask_migration_db = st.checkbox(
    'Ask Migration DB',
    help='Check to consult the Migration database.',
)

ask_spotify_db = st.checkbox(
    'Ask Spotify DB',
    help='Check to consult the Spotify database.',
)

user_input = st.text_input('Write down your question:')


if user_input:
    st.session_state.questions_history.append(user_input)
    history.write("\n".join(st.session_state.questions_history))

    if ask_migration_db:
        st.write('Consulting Migration DB...')
        genai_response, query = ask_postgres(user_input, DB_MIGRATION)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader('SQL Query')
            st.code(query)

        with col2:
            st.subheader('Query Explained')
            st.write(genai_response)

        if st.button('Show DataFrame', key='show_dataframe_migration'):
            df = panda_table_from_query(query, db=DB_MIGRATION)
            if df is not None:
                display_table(df)
            else:
                st.error('Error retrieving DataFrame from Migration DB.')

        if st.button('Show Plot', key='show_plot_migration'):
            df = panda_table_from_query(query, db=DB_MIGRATION)
            if df is not None:
                plot_code = plot_code_from_genai(df)
                display_plot_code(plot_code)
                try:
                    exec(plot_code)
                    st.pyplot(plt)
                except Exception as e:
                    st.error(f'Error executing plot code: {e}')
            else:
                st.error('Error generating DataFrame from Migration DB.')

    elif ask_spotify_db:
        st.write('Consulting Spotify DB...')
        genai_response, query = ask_postgres(
            user_input, DB_SPOTIFY, 'public'
        )

        col1, col2 = st.columns(2)

        with col1:
            st.subheader('SQL Query')
            st.code(query)

        with col2:
            st.subheader('Query Explained')
            st.write(genai_response)

        if st.button('Show DataFrame', key='show_dataframe_spotify'):
            df = panda_table_from_query(
                query, db=DB_SPOTIFY, schema='public'
            )
            if df is not None:
                display_table(df)
            else:
                st.error('Error retrieving DataFrame from Spotify DB.')

        if st.button('Show Plot', key='show_plot_spotify'):
            df = panda_table_from_query(
                query, db=DB_SPOTIFY, schema='public'
            )
            if df is not None:
                plot_code = plot_code_from_genai(df)
                display_plot_code(plot_code)
                try:
                    exec(plot_code)
                    st.pyplot(plt)
                except Exception as e:
                    st.error(f'Error executing plot code: {e}')
            else:
                st.error('Error generating DataFrame from Spotify DB.')

    else:
        st.write('Consulting GenAI...')
        genai_response = ask_oci_genai(user_input)

        if genai_response:
            if hasattr(genai_response, 'content'):
                response_text = genai_response.content
            else:
                response_text = str(genai_response)

            for chunk in response_text.split('. '):
                st.write(chunk)
                st.text('...')
                time.sleep(0.5)

