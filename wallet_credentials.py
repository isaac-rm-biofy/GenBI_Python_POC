import os
from dotenv import load_dotenv

load_dotenv()

username = os.environ.get('ADB_USER', None)
password = os.environ.get('PASSWORD', None)
config = './config'
wallet_path = './config'
wallet_password = os.environ.get('WALLET_PASSWORD', None)
DSN = os.environ.get('DSN', None)
