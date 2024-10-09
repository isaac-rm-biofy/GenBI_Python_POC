import logging
import json
import psycopg2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def execute_query(query):
    connection = None
    try:
        connection = psycopg2.connect(
            user='postgres',
            password='iamzack123',
            host='localhost',
            port='5433',
            database='migration_db',
        )

        cursor = connection.cursor()
        logger.info('Executando a query SQL:')
        cursor.execute(query)
        rows = cursor.fetchall()
        logger.info(f'{len(rows)} linhas retornadas pela query.')

        print(json.dumps(rows, indent=4))

    except Exception as e:
        logger.error(f'Erro ao executar a query: {str(e)}')
    finally:
        if connection:
            cursor.close()
            connection.close()


if __name__ == '__main__':
    logger.info('Iniciando o script...')
    execute_query('SELECT * FROM migration LIMIT 10;')
