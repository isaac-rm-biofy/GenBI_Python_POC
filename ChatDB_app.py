import streamlit as st
import time
import matplotlib.pyplot as plt
from askPostgres import (
    ask_oci_genai,
    panda_table_from_query,
    plot_code_from_genai,
    ask_postgres,
)


def display_table(df):
    """Exibe um DataFrame pandas como uma tabela no Streamlit."""
    st.write(df)


def display_plot_code(code):
    """Exibe o código para plotagem em um bloco de código no Streamlit."""
    st.code(code, language='python')


st.title('ChatDB - Interacting with a GenAI Database')

st.write('### Ask:')
ask_db = st.checkbox(
    'Ask DB',
    help='Check to consult your database and uncheck to ask GenAI.',
)

user_input = st.text_input('Write down your question:')

if user_input:
    if ask_db:
        st.write('Generating SQL query...')
        query = ask_postgres(user_input)
        st.write(f'SQL query generated: `{query}`')

        if st.button('Show DataFrame', key='show_dataframe_button'):
            df = panda_table_from_query(query)
            if df is not None:
                display_table(df)
            else:
                st.error('Error retrieving DataFrame.')

        if st.button('Show Plot', key='show_plot_button_1'):
            df = panda_table_from_query(query)
            if df is not None:
                plot_code = plot_code_from_genai(df)
                #display_plot_code(plot_code)
                try:
                    exec(plot_code)
                    st.pyplot(plt)
                except Exception as e:
                    st.error(f'Error executing plot code: {e}')
            else:
                st.error('Error generating DataFrame from query.')

    else:
        st.write('Consulting GenAI...')
        response = ask_oci_genai(user_input)

        if response:
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)

            for chunk in response_text.split('. '):
                st.write(chunk)
                st.text('...')
                time.sleep(0.5)
