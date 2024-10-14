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
from langchain.chains import create_sql_query_chain

# from pydantic import BaseModel, Field
#from langchain.agents import create_sql_agent
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


def get_table_headers(db, schema="public", sample_limit=6):
    """
    Gera uma string formatada com o nome das tabelas, colunas e até 6 amostras de cada tabela.
    """
    table_info_str = ""
    tables_and_columns = get_schema_tables_and_columns(db, schema)

    for table, columns in tables_and_columns.items():
        query = f"""
        SELECT *
        FROM {schema}.{table}
        LIMIT {sample_limit}
        """
        try:
            df = pd.read_sql(query, db._engine)
            table_info_str += f"Tabela: {table}\n"
            table_info_str += "\t".join(df.columns) + "\n"

            for index, row in df.iterrows():
                table_info_str += "\t".join(map(str, row.values)) + "\n"
            table_info_str += "\n"

        except Exception as e:
            logging.error(f"Erro ao obter a amostra da tabela {table}: {e}")
            table_info_str += f"Tabela: {table} (erro ao obter dados)\n\n"
    return table_info_str


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
        model_id='cohere.command-r-plus', #
        service_endpoint=c.DEFAULT_GENAI_SERVICE_ENDPOINT,
        compartment_id=c.DEFAULT_COMPARTMENT_ID,
        model_kwargs={
            'max_tokens': c.MAX_TOKENS,
            'temperature': 0.1,
        },
        client=client,
    )
    return model


def sql_agent(llm, db=None, db_schema="public"):
    chain = create_sql_query_chain(llm, db)
    table_info_str = get_table_headers(db, db_schema)

    prompt = ChatPromptTemplate.from_messages(
        [("system", c.system), ("human", "{query}")]
    ).partial(
        dialect=db.dialect,
        schema=db_schema,
        table_info=table_info_str,
    )
    validation_chain = prompt | llm | StrOutputParser()
    full_chain = {"query": chain} | validation_chain

    return full_chain
