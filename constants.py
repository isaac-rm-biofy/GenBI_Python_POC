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
SPOTIFY_DATABASE_URI: str = os.environ.get('SPOTIFY_DB_URI', None)
SCHEMA: str = os.environ.get('DB_SCHEMA')
OCI_CREDENTIALS = get_oci_credentials_from_env()
IS_OCI_CREDENTIALS_VALID = all(
    OCI_CREDENTIALS.get(k)
    for k in ('user', 'key_content', 'fingerprint', 'tenancy', 'region')
) and not oci.config.validate_config(OCI_CREDENTIALS)


# CSV FILES PATH
LOCAL = os.getcwd()
SPOTIFY_DATA_TRACKS = LOCAL + '/data.csv'
SPOTIFY_DATA_ARTISTS = LOCAL + '/artists.csv'
SPOTIFY_DATA_LISTENERS = LOCAL + '/listeners.csv'


system = """
You are an agent designed to interact with a SQL database. Below is a list of tables and their corresponding columns from the {schema} schema that you can query:

{table_info}

Always refer to these tables when generating SQL queries. You should never reference tables or columns that are not present in the list above.
You MUST returno only the query.

Never include a LIMIT in the query unless explicitly instructed otherwise. When selecting all columns, use 'SELECT *'. Your task is to:
1. Analyze the input question.
2. Generate a SQL query that is syntactically correct and relevant to the schema provided.
3. Return the SQL query and the query results.

If the user asks to order the results by specific columns, ensure that you include an 'ORDER BY' clause based on the input provided.
DO NOT use Markdown or a codeblock environment.
DO NOT write ```sql in the beginning of your response. 
Your response MUST be a PLAIN SQL STATEMENT ONLY. 
If there are any of the above mistakes, rewrite the query.
"""



PLOT_PROMPT = """Here is a sample of dataset where we show the head and 10 entries of the DataFrame: 
{df_head}
Please generate a complete Python code to create the most suitable type of graph using this dataframe's variables.
In your code you MUST refer to this dataframe as df and treat it as it is already defined this way.
Ensure to remove rows with NaN values. 
You might select some kind of plots to that illustrates interesting relations between 2, 3 or 4 variables of this dataframe.
Examples of plots you can use are {plots}.
The figure should have the standard size (11, 7). 
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
