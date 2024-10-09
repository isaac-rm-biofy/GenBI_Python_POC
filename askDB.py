import re
import logging
import oracledb
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from constants import PROMPT, ACTIONS, PROFILE
from wallet_credentials import (
    username,
    password,
    config,
    wallet_path,
    wallet_password,
    DSN,
)

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'
)


def generate_chat_response(
    profile_name, action=ACTIONS[1], prompt=PROMPT[2], df=None
):
    if df is not None:
        df = df.dropna()

    column_names = df.columns
    df_to_plot = df.head(10)
    table_string = df_to_plot.to_string()

    try:
        with oracledb.connect(
            user=username,
            password=password,
            dsn=DSN,
            config_dir=config,
            wallet_location=wallet_path,
            wallet_password=wallet_password,
        ) as connection:
            with connection.cursor() as cursor:
                query = """
                SELECT DBMS_CLOUD_AI.GENERATE(
                    prompt => :prompt,
                    profile_name => :profile_name,
                    action => :action
                )
                FROM dual
                """

                if prompt == PROMPT[2]:
                    prompt_for_graph = prompt.format(
                        columnNames=column_names, table_string=table_string
                    )
                    logging.debug(
                        f'Passing, profile name as {profile_name}, action as {action}'
                    )
                    logging.debug(f'Passing prompt as {prompt}')
                    cursor.execute(
                        query, [prompt_for_graph, profile_name, action]
                    )
                    llm_response = cursor.fetchone()[0]
                    logging.info('Prompt being sent to LLM: %s', llm_response)
                else:
                    logging.debug(
                        f'Passing, profile name as {profile_name}, action as {action}'
                    )
                    logging.debug(f'Passing prompt as {prompt}')
                    cursor.execute(query, [prompt, profile_name, action])
                    llm_response = cursor.fetchone()[0]
                    logging.info('LLM response: %s', llm_response)

                if isinstance(llm_response, oracledb.LOB):
                    logging.debug('Response is a LOB, reading content.')
                    llm_response = llm_response.read()

                return llm_response
    except oracledb.Error as e:
        logging.error('Error in generating response: %s', e)
    return None


def generate_pandas_table(query):
    try:
        logging.info('Executing query to fetch data for pandas table.')

        with oracledb.connect(
            user=username,
            password=password,
            dsn=DSN,
            config_dir=config,
            wallet_location=wallet_path,
            wallet_password=wallet_password,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                columns = np.array([col[0] for col in cursor.description])
                data = cursor.fetchall()
                df = pd.DataFrame(data, columns=columns)

                logging.info('Pandas DataFrame created successfully.')
                return df

    except oracledb.Error as e:
        logging.error('Error executing query for pandas table: %s', e)
        return None


def generate_plot(profile_name, df, action=ACTIONS[1], prompt=PROMPT[2]):
    logging.info('Generating plot suggested by GenAI.')
    logging.debug(
        f'Profile name: {profile_name}, Action: {action}, Prompt: {prompt}'
    )

    llm_response = generate_chat_response(profile_name, action, prompt, df)
    logging.debug('LLM Response:\n%s', llm_response)

    fig, ax = plt.subplots()

    if llm_response:
        python_code = re.search(r'```python(.*?)```', llm_response, re.DOTALL)

        if python_code:
            python_code = python_code.group(1).strip()
            logging.debug(
                f'Python code extracted from GenAI response:\n{python_code}'
            )

            modified_code = re.sub(
                r'dados\s*=\s*\{.*?}', 'df = df', python_code, flags=re.DOTALL
            )

            modified_code = modified_code.replace('plt.show()', '')

            logging.debug('Modified code to execute:\n%s', modified_code)

            try:
                exec(modified_code, globals(), locals())
            except Exception as exec_error:
                logging.error(f'Error in Python execution: {exec_error}')

            if plt.gca().has_data():
                logging.info('Plot generation successful.')
                # plt.show()
                return fig
            else:
                logging.warning('No data plotted.')
                plt.close(fig)
                return None
        else:
            logging.warning('No Python code was found in GenAI response.')
            plt.close(fig)
            return None
    else:
        logging.error('No GenAI answer for plot generation.')
        plt.close(fig)
        return None


def generate_query(prompt, action, profile_name):
    try:
        logging.info('Starting connection to Oracle-ADB.')

        with oracledb.connect(
            user=username,
            password=password,
            dsn=DSN,
            config_dir=config,
            wallet_location=wallet_path,
            wallet_password=wallet_password,
        ) as connection:
            logging.info('Connection established.')
            with connection.cursor() as cursor:
                query = """
                SELECT DBMS_CLOUD_AI.GENERATE(
                    prompt => :prompt,
                    profile_name => :profile_name,
                    action => :action
                )
                FROM dual
                """

                logging.debug('Executing NL consult.')
                cursor.execute(query, [prompt, profile_name, action])
                nl_response = cursor.fetchone()[0]
                logging.info('NL consult done.')

                if isinstance(nl_response, oracledb.LOB):
                    logging.debug('Response is type LOB.')
                    nl_response = nl_response.read()

                logging.info('SQL query generated with success.')
                df = generate_pandas_table(nl_response)

                return nl_response, df

    except oracledb.Error as e:
        logging.error('Error in generating response: %s', e)
        return None


if __name__ == '__main__':
    logging.info('Chamando chatDB.')

    result, df = generate_query(PROMPT[0], ACTIONS[0], PROFILE)
    logging.info('Resposta: %s', result)

    if df is not None:
        generate_plot(PROFILE, df)
        plt.show()
