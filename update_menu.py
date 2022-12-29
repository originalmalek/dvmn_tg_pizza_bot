from dotenv import load_dotenv

from main import get_database_connection
from motlin_api import get_products


def upload_menu_to_redis(menu):
    db.set('menu', str(menu))


if __name__ == '__main__':
    load_dotenv()
    db = get_database_connection()

    menu = get_products()
    upload_menu_to_redis(menu)
