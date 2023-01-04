import os
import logging
import json

import requests

from telegram_logger import MyLogsHandler

from dotenv import load_dotenv
from flask import Flask, request

from get_database_connection import get_database_connection

from facebook_markup import create_product_carousel, create_first_templates_of_menu, create_last_template_of_menu, \
    create_first_templates_of_cart, create_cart_templates
from motlin_api import add_item_to_cart, get_cart, delete_cart_item

app = Flask(__name__)
logger = logging.getLogger('FB ElasticPath Bot')


@app.route('/', methods=['GET'])
def verify():
    """
    При верификации вебхука у Facebook он отправит запрос на этот адрес. На него нужно ответить VERIFY_TOKEN.
    """
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():
    """
    Основной вебхук, на который будут приходить сообщения от Facebook.
    """
    db = get_database_connection()

    data = request.get_json()
    sender_id = data['entry'][0]['messaging'][0]['sender']['id']
    user_state = db.hget(f'facebook_{sender_id}', 'user_state')

    if user_state is None:
        new_user_state = send_menu(sender_id)

    if user_state.decode('utf-8') == 'menu':
        new_user_state = handle_main_menu(data, sender_id)

    if user_state.decode('utf-8') == 'cart':
        new_user_state = handle_cart(data, sender_id)

    db.hset(f'facebook_{sender_id}', 'user_state', new_user_state)
    return "ok", 200


def handle_cart(data, sender_id):
    if 'postback' in data['entry'][0]['messaging'][0]:
        payload = data['entry'][0]['messaging'][0]['postback']['payload']
        return handle_payload(payload, sender_id, 'cart')
    else:
        send_message(sender_id, 'Неверная команда')
        send_cart(sender_id)
        return 'cart'


def handle_payload(payload, sender_id, user_state):

    payload = eval(payload)

    if 'action' in payload:
        action = payload['action']

        if action == 'cart':  # корзина
            send_cart(sender_id)
            return 'cart'

        if action == 'rich':  # сытные пиццы
            send_menu(sender_id, pizzas_type='rich')

        if action == 'special':  # специальные пиццы
            send_menu(sender_id, pizzas_type='special')

        if action == 'main' or action == 'menu':  # основные пиццы
            send_menu(sender_id, pizzas_type='main')

        if action == 'hot':  # острые пиццы
            send_menu(sender_id, pizzas_type='hot')

        return 'menu'

    if 'add_to_cart' in payload:
        add_item_to_cart(payload['add_to_cart'], 1, f'facebook_{sender_id}')
    if 'del_from_cart' in payload:
        delete_cart_item(f'facebook_{sender_id}', payload['del_from_cart'])
    if user_state == 'cart':
        send_cart(sender_id)
    if user_state == 'menu':
        send_menu(sender_id)
    return user_state



def handle_main_menu(data, sender_id):
    if 'postback' in data['entry'][0]['messaging'][0]:
        payload = data['entry'][0]['messaging'][0]['postback']['payload']
        return handle_payload(payload, sender_id, 'menu')
    else:
        send_message(sender_id, 'Неверная команда')
        send_menu(sender_id)
        return 'menu'


def send_cart(sender_id):
    user_cart = get_cart(f'facebook_{sender_id}')

    params = {"access_token": os.environ['FACEBOOK_PAGE_ACCESS_TOKEN']}
    headers = {"Content-Type": "application/json"}

    cart_carousel = create_first_templates_of_cart(user_cart['meta']['display_price']['with_tax']['amount']) + \
                    create_cart_templates(user_cart)

    json_data = {
        'recipient': {
            'id': sender_id,
        },
        'message': {
            'attachment': {
                'type': 'template',
                'payload': {
                    'template_type': 'generic',
                    'elements': cart_carousel,
                },
            },
        },
    }

    response = requests.post('https://graph.facebook.com/v2.6/me/messages',
                             headers=headers, json=json_data, params=params)
    response.raise_for_status()
    return 'main'


def send_message(recipient_id, message_text):
    params = {"access_token": os.environ['FACEBOOK_PAGE_ACCESS_TOKEN']}
    headers = {"Content-Type": "application/json"}
    request_content = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    response = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers,
                             data=request_content)
    response.raise_for_status()


def send_menu(sender_id, pizzas_type='main'):
    params = {"access_token": os.environ['FACEBOOK_PAGE_ACCESS_TOKEN']}
    headers = {"Content-Type": "application/json"}

    menu_carousel = create_first_templates_of_menu() + create_product_carousel(pizzas_type) + \
                    create_last_template_of_menu(pizzas_type)

    json_data = {
        'recipient': {
            'id': sender_id,
        },
        'message': {
            'attachment': {
                'type': 'template',
                'payload': {
                    'template_type': 'generic',
                    'elements': menu_carousel,
                },
            },
        },
    }

    response = requests.post('https://graph.facebook.com/v2.6/me/messages',
                             headers=headers, json=json_data, params=params)
    response.raise_for_status()
    return 'menu'


if __name__ == '__main__':
    load_dotenv()
    ep_store_id = os.getenv('EP_STORE_ID')
    ep_client_id = os.getenv('EP_CLIENT_ID')
    ep_client_secret = os.getenv('EP_CLIENT_SECRET')
    telegram_api_key = os.getenv('TELEGRAM_API_KEY')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    my_log_handler = MyLogsHandler(level=logging.DEBUG, telegram_token=telegram_api_key,
                                   chat_id=telegram_chat_id)
    logging.basicConfig(level=20)
    logger.addHandler(my_log_handler)

    try:
        logger.warning('Bot FB is working')
        app.run(debug=True)
    except Exception as err:
        logger.exception('Bot FB got an error')
