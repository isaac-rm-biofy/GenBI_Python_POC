import logging
import re

import pandas as pd
from langchain_community.utilities import SQLDatabase

from constants import (
    SQLALCHEMY_DATABASE_URI,
    SPOTIFY_DATABASE_URI,
    PLOT_PROMPT,
)
from utils import get_llm_model, sql_agent, validate_query

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()],
)

# CHAMANDO O MODELO
LLM = get_llm_model()

# DATABASES ACESSÍVEIS
DB_MIGRATION = SQLDatabase.from_uri(SQLALCHEMY_DATABASE_URI)
DB_SPOTIFY = SQLDatabase.from_uri(SPOTIFY_DATABASE_URI)



def ask_oci_genai(question: str):
    try:
        llm_response = LLM.invoke(question)
        return llm_response
    except Exception as e:
        logging.error(f'Erro ao consultar GenAI: {e}')
        raise e


def panda_table_from_query(query: str, db, schema: str = None):
    try:
        if schema:
            query = query.replace('FROM ', f'FROM {schema}.')
        df = pd.read_sql(query, db._engine)
        return df
    except Exception as e:
        logging.error(f'Erro ao executar a query SQL: {e}')
        raise e


def plot_code_from_genai(df: pd.DataFrame):
    try:
        head = df.head(10).to_string(index=False)
        PLOT_LIST = [
            'histogram',
            'lineplot',
            'scatterplot',
            'heatmap',
            'boxplot',
        ]

        prompt = PLOT_PROMPT.format(df_head=head, plots=PLOT_LIST)
        logging.info(f'O prompt passado à LLM: {prompt}')

        response = LLM.invoke(prompt)
        logging.info(f'A resposta da LLM: {response}')

        if response:
            python_code = re.search(
                r'```python(.*?)```', response.content, re.DOTALL
            )

            if python_code:
                python_code = python_code.group(1).strip()
                logging.debug(
                    f'Python code extracted from GenAI response:\n{python_code}'
                )
                modified_code = re.sub(
                    r'dados\s*=\s*\{.*?}',
                    'df = df',
                    python_code,
                    flags=re.DOTALL,
                )
                # modified_code = modified_code.replace("plt.show()", "")
                logging.debug('Modified code to execute:\n%s', modified_code)

        return modified_code
    except Exception as e:
        logging.error(f'Erro ao gerar código de plotagem: {e}')
        raise e


# def ask_postgres(question: str, db, schema='public'):
#     logging.info(f'Consultando SQL agent com a pergunta: {question}')
#     SQL_AGENT = sql_agent(LLM, db, schema)
#     try:
#         my_query = SQL_AGENT.invoke({'question': question})
#         logging.info(f'Resposta da GenAI: {my_query}')
#         return my_query
#     except Exception as e:
#         logging.error(f'Erro ao consultar o SQL agent: {e}')
#         raise e
def ask_postgres(question: str, db, schema="public"):
    logging.info(f"Consultando SQL agent com a pergunta: {question}")
    SQL_AGENT = sql_agent(LLM, db, schema)

    try:
        my_query = SQL_AGENT.invoke({"question": question})
        logging.info(f"Resposta da GenAI: {my_query}")
        if validate_query(my_query, db, schema):
            return my_query
        else:
            logging.error(
                "Query inválida gerada pela GenAI. A execução foi interrompida."
            )
            return None

    except Exception as e:
        logging.error(f"Erro ao consultar o SQL agent: {e}")
        raise e




if __name__ == '__main__':
    try:

        my_resp = ask_postgres(
            'todas os os artistas com músicas explicitas em 2001', DB_SPOTIFY, 'spotify_schema'
        )
        my_table = panda_table_from_query(my_resp, DB_SPOTIFY)
        print(my_table)
        my_plot_code = plot_code_from_genai(my_table)
        print(my_plot_code)

    except Exception as e:
        logging.error(f"Erro ao consultar a GenAI com SQL Agent: {e}")
