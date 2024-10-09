import streamlit as st
import logging
from askDB import (
    generate_query,
    generate_chat_response,
    generate_plot,
    PROFILE,
    ACTIONS,
)

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'
)

st.title('ChatDB')

user_input = st.text_area('Faça sua pergunta:')
ask_db = st.checkbox('Ask DB')

st.markdown('### Resposta da GenAI')


def clear_session():
    st.session_state.clear()


if st.button('Enviar'):
    clear_session()

    if ask_db:
        st.write('Consultando o banco de dados...')
        result = generate_query(user_input, ACTIONS[0], PROFILE)

        if result:
            query_generated, df = result
            st.session_state['query_generated'] = query_generated
            st.session_state['df'] = df

            st.markdown('**Query gerada pela GenAI:**')
            st.code(query_generated)
        else:
            st.warning('Nenhum resultado foi retornado para a consulta.')
    else:
        st.write('Consultando a GenAI...')
        llm_response = generate_chat_response(
            PROFILE, action=ACTIONS[1], prompt=user_input
        )

        if llm_response:
            st.markdown('**Resposta da GenAI:**')
            st.write(llm_response)
        else:
            st.warning('Nenhuma resposta foi retornada da GenAI.')

# Exibir tabela se disponível
if 'df' in st.session_state:
    if st.button('Ver tabela'):
        st.write('**Tabela gerada pela consulta:**')
        st.dataframe(st.session_state['df'])

if 'df' in st.session_state:
    if st.button('Ver plot'):
        st.write('**Plot gerado pela consulta:**')
        if 'fig' not in st.session_state:
            # Chama a função generate_plot e armazena a figura
            fig = generate_plot(PROFILE, st.session_state['df'])
            st.session_state['fig'] = fig

        if st.session_state['fig']:
            st.pyplot(st.session_state['fig'])
        else:
            st.warning('Nenhum gráfico foi gerado.')
