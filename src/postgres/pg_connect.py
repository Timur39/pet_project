import os

from asyncpg_lite import DatabaseManager
from dotenv import load_dotenv
from sqlalchemy.testing.config import db_opts

load_dotenv()

# password = os.getenv('PG_PASS')
# host = os.getenv('PG_HOST')
# name = os.getenv('PG_NAME')
# port = os.getenv('PG_PORT')
# user = os.getenv('PG_USER')
# params = {'user': user, 'password': password, 'host': host, 'port': port, 'database': name}
link = os.getenv('PG_LINK')
pg_manager = DatabaseManager(db_url=link, deletion_password=os.getenv('ROOT_PASS'))
