import logging

import oci
import pandas as pd
from dotenv import load_dotenv
from langchain.chains import TransformChain

# from langchain_core.tools import Tool
from langchain_community.chat_models import ChatOCIGenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

import constants as c

# from pydantic import BaseModel, Field
# from langchain.agents import create_sql_agent
# from langchain.agents.agent_toolkits import SQLDatabaseToolkit
# from langchain.agents.agent_types import AgentType


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


def get_table_headers(db, schema='public', limit=5):
    headers = {}
    tables_and_columns = get_schema_tables_and_columns(db, schema)
    for table, columns in tables_and_columns.items():
        query = f"""
        SELECT *
        FROM {schema}.{table}
        LIMIT {limit}
        """
        try:
            df = pd.read_sql(query, db._engine)
            headers[table] = df
        except Exception as e:
            logging.error(f'Erro ao obter o cabeçalho da tabela {table}: {e}')
            headers[table] = None
    return headers

def validate_query(query: str, db, schema="public") -> bool:
    schema_info = get_schema_tables_and_columns(db, schema)

    for table in schema_info.keys():
        if table in query:
            columns = schema_info[table]
            for column in columns:
                if column not in query:
                    logging.error(f"A coluna {column} não existe na tabela {table}")
                    return False
    logging.info("A query é válida.")
    return True


def get_llm_model():
    if not c.IS_OCI_CREDENTIALS_VALID:
        return
    client = oci.generative_ai_inference.GenerativeAiInferenceClient(
        config=c.OCI_CREDENTIALS,
        service_endpoint=c.DEFAULT_GENAI_SERVICE_ENDPOINT,
    )
    model = ChatOCIGenAI(
        model_id='meta.llama-3.1-405b-instruct', #'cohere.command-r-plus', #
        service_endpoint=c.DEFAULT_GENAI_SERVICE_ENDPOINT,
        compartment_id=c.DEFAULT_COMPARTMENT_ID,
        model_kwargs={
            'max_tokens': c.MAX_TOKENS,
            'temperature': 0.1,
        },
        client=client,
    )
    return model


# def sql_agent(llm, db=None, db_schema='public'):
#     chain = create_sql_query_chain(llm, db)
#     prompt = ChatPromptTemplate.from_messages(
#         [('system', c.system), ('human', '{query}')]
#     ).partial(
#         dialect=db.dialect,
#         table_info=get_table_headers(db, db_schema),
#     )
#     print(get_table_headers(db, db_schema))
#     validation_chain = prompt | llm | StrOutputParser()
#     full_chain = {'query': chain} | validation_chain
#     # full_chain.get_prompts()[0].pretty_print()
#     return full_chain
# Função para capturar tabelas e colunas corretamente


def sql_agent(llm, db=None, db_schema="public"):
    tables_info = get_schema_tables_and_columns(db, db_schema)
    prompt = ChatPromptTemplate.from_messages(
        [("system", "You are a SQL expert."), ("human", "{query}")]
    ).partial(
        dialect=db.dialect,
        table_info=tables_info,
    )
    validation_chain = TransformChain(prompt | llm | StrOutputParser())
    return validation_chain

