import logging
import re
import pandas as pd
from langchain_community.utilities import SQLDatabase
from constants import SQLALCHEMY_DATABASE_URI, PLOT_PROMPT
from utils import get_llm_model, sql_agent


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()],
)

LLM = get_llm_model()
DB = SQLDatabase.from_uri(SQLALCHEMY_DATABASE_URI)
SQL_AGENT = sql_agent(LLM, DB)


def ask_oci_genai(question: str):
    try:
        llm_response = LLM.invoke(question)
        return llm_response
    except Exception as e:
        logging.error(f'Erro ao consultar GenAI: {e}')
        raise e


def panda_table_from_query(query: str):
    try:
        df = pd.read_sql(query, DB._engine)
        return df
    except Exception as e:
        logging.error(f'Erro ao executar a query SQL: {e}')
        raise e


def plot_code_from_genai(df: pd.DataFrame):
    try:
        table_string = df.head(15).to_string(index=False)
        column_names = df.columns.tolist()
        prompt = PLOT_PROMPT.format(
            columnNames=column_names, table_string=table_string
        )
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


def ask_postgres(question: str):
    logging.info(f'Consultando SQL agent com a pergunta: {question}')
    try:
        my_query = SQL_AGENT.invoke({'question': question})
        logging.info(f'Resposta da GenAI: {my_query}')
        return my_query
    except Exception as e:
        logging.error(f'Erro ao consultar o SQL agent: {e}')
        raise e


if __name__ == '__main__':

    try:
        my_resp = ask_postgres(
            "filter the table for country and total migration for year equal to 2020"
        )
        my_table = panda_table_from_query(my_resp)
        my_plot_code = plot_code_from_genai(my_table)
        print(my_plot_code)

    except Exception as e:
        logging.error(f'Erro ao consultar a GenAI com SQL Agent: {e}')
