import os
import sys
import json
from datetime import datetime

import requests
from flask import Flask, request
from facebook_markup import create_product_carousel, create_first_page_of_carousel
app = Flask(__name__)


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
    data = request.get_json()
    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                if messaging_event.get("message"):  # someone sent us a message
                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text
                    # send_message(sender_id, message_text)
                    send_keyboard(sender_id)

    return "ok", 200


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
    response = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=request_content)
    response.raise_for_status()


def send_menu():
    pass


def send_keyboard(sender_id):
    params = {"access_token": os.environ['FACEBOOK_PAGE_ACCESS_TOKEN']}
    headers = {"Content-Type": "application/json"}
    # menu_carousel = create_first_page_of_carousel().append(create_product_carousel())
    menu_carousel = create_first_page_of_carousel() + create_product_carousel()

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

    response = requests.post('https://graph.facebook.com/v2.6/me/messages', headers=headers, json=json_data, params=params)
    response.raise_for_status()


if __name__ == '__main__':
    app.run(debug=True)