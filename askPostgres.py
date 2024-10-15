import logging
import re
import pandas as pd
from langchain_community.utilities import SQLDatabase
from constants import (
    SQLALCHEMY_DATABASE_URI,
    SPOTIFY_DATABASE_URI,
    PLOT_PROMPT,
)
from utils import get_llm_model, my_sql_agent, SQLHandler


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()],
)


# CHAMANDO O MODELO
LLM = get_llm_model(OPENAI=True)
logging.info(f'Tipo de LLM: {type(LLM)}')

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


def ask_postgres(question: str, db, schema='public'):
    handler = SQLHandler()
    logging.info(f'Consultando SQL agent com a pergunta: {question}')
    SQL_AGENT = my_sql_agent(LLM, db, schema)

    try:
        # agent_response = SQL_AGENT.invoke(question, return_query=True, callbacks=[handler])
        agent_response = SQL_AGENT.run(
            {'input': question}, callbacks=[handler]
        )
        sql_queries = handler.sql_result[-1]

        return agent_response, sql_queries['query']

    except Exception as e:
        logging.error(f'Erro ao consultar o SQL agent: {e}')
        raise e


if __name__ == '__main__':
    try:
        response_data, sql_queries = ask_postgres(
            'mostre os artistas por streams diárias com menos colaborações, i.e., as_features',
            DB_SPOTIFY,
            'public'
        )
        print('Resposta: ', response_data)
        print('query:', sql_queries)

    except Exception as e:
        logging.error(f'Erro na execução: {e}')
