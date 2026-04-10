import os
import pymysql
from dbutils.pooled_db import PooledDB
from dotenv import load_dotenv

load_dotenv()

_pool = PooledDB(
    creator=pymysql,
    maxconnections=10,
    mincached=2,
    maxcached=5,
    blocking=True,
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    database=os.getenv("DB_NAME"),
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=False,
)

def get_connection():
    return _pool.connection()
