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
AMAZONIA_API_KEY = os.environ.get('AMAZONIA_API_KEY', None)
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

system = """You are an agent designed to interact with a SQL database. Given an input question, create a syntactically correct SQL query to run, then look at the results of the query and return the answer.
You MUST include the original SQL query used to generate the answer in the output.
Below is a list of tables, their columns, and sample rows from the schema {schema}. Each table contains important information such as:

- **Table Name**: The name of the table you should query.
- **Columns**: The names of the columns in each table.
- **Sample Data**: Example rows of data from each table to help you understand the type of information stored (e.g., text, numbers, dates) and their meaning.

Here is the list of tables and their sample data:

{table_info}

Use this information to:
1. **Understand the content** of each table, including the **table name**, **columns**, and **the type of data** stored in each column. Pay attention to the **meaning of the data** in the context of the table.
2. **Generate a valid SQL query** that retrieves data according to the user's input and the schema provided.

You MUST return only the query without any explanations, text, or commentary. Ensure that:
- The query is valid SQL for the database schema provided.
- You do not include a LIMIT unless specifically requested.
- Use 'SELECT *' when selecting all columns.
- If asked to order by specific columns, include the appropriate 'ORDER BY' clause.

IMPORTANT: 
- DO NOT include any text, explanations, or markdown formatting such as ```sql.
- Your response MUST contain ONLY a valid SQL query, with no additional information.

If the response includes anything other than a plain SQL query, rewrite the query and remove all extraneous text.
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
