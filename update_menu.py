import redis
import requests

from dotenv import load_dotenv
import os
from motlin_api import get_products
from datetime import datetime
_database = None

def get_database_connection():
    global _database
    if _database is None:
        database_password = os.getenv('DATABASE_PASSWORD')
        database_host = os.getenv('DATABASE_HOST')
        database_port = os.getenv('DATABASE_PORT')
        _database = redis.Redis(host=database_host, port=database_port, password=database_password)
    return _database


def upload_menu_to_redis():
    menu = get_products()
    db.set('menu', str(menu))
    print(db.get('menu'))


if __name__ == '__main__':
    load_dotenv()
    db = get_database_connection()

    cached_menu = db.get('menu')
    time_diff = datetime.now() - cached_menu['created_at']
    if time_diff.hours > 0:
        upload_menu_to_redis()
    else:
        menu = cached_menu
