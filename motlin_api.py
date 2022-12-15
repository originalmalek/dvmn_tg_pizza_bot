import json
import os

import requests

from datetime import datetime
from dotenv import load_dotenv


EP_ACCESS_TOKEN = None
EP_TOKEN_TIME = None

def get_access_token():
	global EP_ACCESS_TOKEN
	global EP_TOKEN_TIME

	if not EP_ACCESS_TOKEN or datetime.now().timestamp() >= EP_TOKEN_TIME - 30:  #30 sec is reserve
		data = {
			'client_id': os.getenv('EP_CLIENT_ID'),
			'client_secret': os.getenv('EP_CLIENT_SECRET'),
			'grant_type': 'client_credentials',
		}

		response = requests.post('https://api.moltin.com/oauth/access_token', data=data)
		response.raise_for_status()
		response_json = response.json()
		EP_ACCESS_TOKEN = response_json['access_token']
		EP_TOKEN_TIME = response_json['expires']
	return EP_ACCESS_TOKEN


def get_cart(chat_id):
	headers = {
		'Authorization': get_access_token(),
	}
	response = requests.get(f'https://api.moltin.com/v2/carts/{chat_id}/items', headers=headers)
	response.raise_for_status()
	return response.json()


def get_products():
	headers = {
		'Authorization': get_access_token(),
	}

	response = requests.get('https://api.moltin.com/v2/products', headers=headers)
	response.raise_for_status()
	return response.json()


def add_item_to_cart(product_sku, quantity, chat_id):
	cart_id = chat_id
	headers = {
		'Authorization': get_access_token(),
		'Content-Type': 'application/json',
	}

	json_data = {"data": {"sku": f"{product_sku}", "type": "cart_item", "quantity": quantity}}

	response = requests.post(f'https://api.moltin.com/v2/carts/{cart_id}/items', headers=headers, json=json_data)
	response.raise_for_status()
	return response.json()


def delete_cart_item(query):
	headers = {
		'Authorization': get_access_token(),
	}
	product_id = json.loads(query.data)['id']
	response = requests.delete(f'https://api.moltin.com/v2/carts/{query.message.chat_id}/items/{product_id}',
	                           headers=headers)
	response.raise_for_status()
	return response.json()


def add_order_to_crm(chat_id, email):
	headers = {
		'Authorization': get_access_token(),
	}

	json_data = {
		'data': {
			'type': 'customer',
			'name': str(chat_id),
			'email': email,
			'password': 'mysecretpassword',
		},
	}

	response = requests.post('https://api.moltin.com/v2/customers', headers=headers, json=json_data)
	response.raise_for_status()


def get_product_data(query):
	headers = {
		'Authorization': get_access_token(),
	}
	product_response = requests.get(f'https://api.moltin.com/v2/products/{query.data}', headers=headers)
	product_response.raise_for_status()
	return product_response.json()['data']


def get_image_url(product_image_id):
	headers = {
		'Authorization': get_access_token(),
	}
	image_response = requests.get(f'https://api.moltin.com/v2/files/{product_image_id}', headers=headers)
	image_response.raise_for_status()

	image_url = image_response.json()['data']['link']['href']
	return image_url


def download_product_picture(product_image_id):
	image_url = get_image_url(product_image_id)

	if not os.path.exists(f'pictures/{product_image_id}.jpeg'):
		with open(f'pictures/{product_image_id}.jpeg', 'wb') as f:
			f.write(requests.get(image_url).content)


def create_entry_client_address(flow_slug, user_id, longitude, latitude):
	headers = {
		'Authorization': f'Bearer {get_access_token()}',
		'Content-Type': 'application/json',
	}

	json_data = {
		'data': {
			'type': 'entry',
			'UserId': user_id,
			'Longitude': longitude,
			'Latitude': latitude,
		},
	}

	response = requests.post(f'https://api.moltin.com/v2/flows/{flow_slug}/entries',
	                         headers=headers, json=json_data)
	response.raise_for_status()


def get_flow(flow_id):
	headers = {
		'Authorization': get_access_token(),
	}

	response = requests.get(f'https://api.moltin.com/v2/flows/{flow_id}', headers=headers)
	response.raise_for_status()
	return response.json()


def get_all_entries(slug):
	headers = {
		'Authorization': get_access_token(),
	}

	response = requests.get(f'https://api.moltin.com/v2/flows/{slug}/entries?page[limit]=100', headers=headers)
	response.raise_for_status()
	return response.json()


def get_all_fields():
	headers = {
		'Authorization': get_access_token(),
	}

	response = requests.get('https://api.moltin.com/v2/fields', headers=headers)
	response.raise_for_status()
	return response.json()


if __name__ == '__main__':
    load_dotenv()
