import logging
import os
import oci
import pandas as pd
import constants as c
from dotenv import load_dotenv
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.chat_models import ChatOCIGenAI
from langchain_core.messages import SystemMessage
from langchain.callbacks.base import BaseCallbackHandler
from langchain_openai import ChatOpenAI


load_dotenv()


def get_tables(db, schema='public'):
    query = f"""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_type = 'BASE TABLE' AND table_schema = '{schema}'
    """
    try:
        df = pd.read_sql(query, db._engine)
        tables = df['table_name'].values.tolist()
        return tables
    except Exception as e:
        logging.error(f'Erro ao obter tabelas do banco de dados: {e}')
        return []


def get_columns_for_table(db, table_name):
    query = f"""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = '{table_name}'
    """
    try:
        df = pd.read_sql(query, db._engine)
        return df['column_name'].tolist()
    except Exception as e:
        logging.error(f'Erro ao obter colunas para a tabela {table_name}: {e}')
        return []


def get_schema_tables_and_columns(db, schema='public'):
    tables_and_columns = {}
    tables = get_tables(db, schema)
    for table in tables:
        columns = get_columns_for_table(db, table)
        tables_and_columns[table] = columns
    return tables_and_columns


def get_table_headers(db, schema='public', sample_limit=6):

    table_info_str = ''
    tables_and_columns = get_schema_tables_and_columns(db, schema)

    for table, columns in tables_and_columns.items():
        query = f"""
        SELECT *
        FROM {schema}.{table}
        LIMIT {sample_limit}
        """
        try:
            df = pd.read_sql(query, db._engine)
            table_info_str += f'Tabela: {table}\n'
            table_info_str += '\t'.join(df.columns) + '\n'

            for index, row in df.iterrows():
                table_info_str += '\t'.join(map(str, row.values)) + '\n'
            table_info_str += '\n'

        except Exception as e:
            logging.error(f'Erro ao obter a amostra da tabela {table}: {e}')
            table_info_str += f'Tabela: {table} (erro ao obter dados)\n\n'
    return table_info_str


class SQLHandler(BaseCallbackHandler):
    def __init__(self):
        self.sql_result = []

    def on_agent_action(self, action, **kwargs):
        if action.tool in ['sql_db_query_checker', 'sql_db_query']:
            self.sql_result.append(action.tool_input)


def get_llm_model(OPENAI=True):

    if OPENAI:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                'A chave API não foi encontrada. Verifique a variável de ambiente.'
            )

        model = ChatOpenAI(
            api_key=api_key, model='gpt-4o-mini', temperature=0.2
        )
    else:
        if not c.IS_OCI_CREDENTIALS_VALID:
            return
        client = oci.generative_ai_inference.GenerativeAiInferenceClient(
            config=c.OCI_CREDENTIALS,
            service_endpoint=c.DEFAULT_GENAI_SERVICE_ENDPOINT,
        )
        model = ChatOCIGenAI(
            model_id='meta.llama-3.1-405b-instruct',  #'cohere.command-r-plus', #
            service_endpoint=c.DEFAULT_GENAI_SERVICE_ENDPOINT,
            compartment_id=c.DEFAULT_COMPARTMENT_ID,
            model_kwargs={
                'max_tokens': c.MAX_TOKENS,
                'temperature': 0.1,
            },
            client=client,
        )
    return model


def my_sql_agent(llm, db, db_schema):
    table_info = get_table_headers(db, db_schema)
    print(table_info)
    db_toolkit = SQLDatabaseToolkit(db=db, llm=llm)

    prompt_formatted = c.system.format(schema=db_schema, table_info=table_info)
    system_message = SystemMessage(content=prompt_formatted)
    logging.info(f'Prompt formatado: {system_message}')

    my_agent = create_sql_agent(
        llm,
        toolkit=db_toolkit,
        agent_type='openai-tools',
        verbose=True,
        messages_modifier=system_message,
        handle_parsing_errors=True,
        handle_sql_errors=True,
    )

    return my_agent
