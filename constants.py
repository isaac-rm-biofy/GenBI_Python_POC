import os
import oci
from dotenv import load_dotenv

load_dotenv()


def get_env():
    return os.environ.get('ENV', 'dev')


def get_oci_credentials_from_env():
    oci_raw_key = os.environ.get('OCI_API_KEY')
    pem_prefix = '-----BEGIN RSA PRIVATE KEY-----\n'
    pem_suffix = '\n-----END RSA PRIVATE KEY-----'
    oci_pem_key_content = '{}{}{}'.format(pem_prefix, oci_raw_key, pem_suffix)

    return dict(
        user=os.environ.get('OCI_USER_ID'),
        key_content=oci_pem_key_content,
        fingerprint=os.environ.get('OCI_FINGERPRINT'),
        tenancy=os.environ.get('OCI_TENANCY_ID'),
        region=os.environ.get('OCI_REGION'),
    )


def get_postgres_credentials_from_env():
    return dict(
        host=os.environ.get('POSTGRES_HOST', 'localhost'),
        port=os.environ.get('POSTGRES_PORT', 5433),
        user=os.environ.get('POSTGRES_USER'),
        password=os.environ.get('POSTGRES_PASSWORD'),
        db=os.environ.get('POSTGRES_DB', 'migration_db'),
    )


def get_sqlalchemy_database_uri():
    creds = get_postgres_credentials_from_env()
    return f'postgresql://{creds["user"]}:{creds["password"]}@{creds["host"]}:{creds["port"]}/{creds["db"]}'


MAX_TOKENS = int(3600)
DEFAULT_COMPARTMENT_ID = os.environ.get('COMPARTMENT_ID')
DEFAULT_GENAI_SERVICE_ENDPOINT = os.environ.get('GENAI_SERVICE_ENDPOINT')
SQLALCHEMY_DATABASE_URI: str = get_sqlalchemy_database_uri()
OCI_CREDENTIALS = get_oci_credentials_from_env()
IS_OCI_CREDENTIALS_VALID = all(
    OCI_CREDENTIALS.get(k)
    for k in ('user', 'key_content', 'fingerprint', 'tenancy', 'region')
) and not oci.config.validate_config(OCI_CREDENTIALS)


system = """You are an agent designed to interact with a SQL database and tables {tables_names}. 
To start you should ALWAYS look at the tables in the database to see what you can query.
Do NOT skip this step.
Given an input question, create a syntactically correct SQL query, then look at the results of the query and return the answer.
You can order the results by a relevant column to return the most interesting examples in the database.
Only ask for the relevant columns given the question.
Double check the user's {dialect} query for common mistakes, including:
- Using NOT IN with NULL values
- Using UNION when UNION ALL should have been used
- Using BETWEEN for exclusive ranges
- Data type mismatch in predicates
- Properly quoting identifiers
- Using the correct number of arguments for functions
- Casting to the correct data type
- Using the proper columns for joins

You MUST double check your query before executing it. 
If you get an error while executing a query, rewrite the query and try again.
DO NOT use Markdown or a codeblock environment.
DO NOT write ```sql in the beginning of your response. 
Your response MUST be a PLAIN SQL STATEMENT ONLY. 
If there are any of the above mistakes, rewrite the query. 
If there are no mistakes, just reproduce the original query."""


PLOT_PROMPT = """Here is a dataset represented as a DataFrame with the columns: {columnNames}. {table_string}. 
Please generate a complete Python code to create the most suitable type of graph using these variables. 
Ensure to remove rows with NaN values. The figure should have the standard size (11, 7). 
Preferably use matplotlib and matplotlib style ggplot. When creating the figure, remember to name it 'fig'; for bar charts, make them horizontal 
and always generate legends."""



######################################## CONSTANTS FOR CHATDB USING ADB OCI ##############################################

PROMPT = [
    'filter the table MIGRATION for year equal to 1995 and select all',
    'quantas copas do mundo o brasil tem?',
    'Aqui está um conjunto de dados representado como um DataFrame com as colunas: {columnNames}. {table_string}. '
    + 'Por favor, gere um código Python completo para fazer o tipo de gráfico mais adequado usando essas variáveis. '
    + 'Garanta eliminar linhas com NaN values. '
    + 'A figura deve ter o tamanho padrão (11, 7). Use preferencialmente o matplotlib. '
    + "Ao criar a figura, lembre-se de nomeá-la 'fig', para gráficos de barra façam com que elas estejam na horizontal e sempre gerar legendas.",
]

ACTIONS = ['showsql', 'chat', 'narrate']
PROFILE = 'OCI_COHERE_COMMAND_R_PLUS'
