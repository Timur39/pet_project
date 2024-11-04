import os

from asyncpg_lite import DatabaseManager
from dotenv import load_dotenv

load_dotenv()

pg_manager = DatabaseManager(db_url=os.getenv('PG_LINK'), deletion_password=os.getenv('ROOT_PASS'))
