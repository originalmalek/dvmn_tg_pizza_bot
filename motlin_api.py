import json
import os

import requests

from datetime import timedelta, datetime


EP_ACCESS_TOKEN = None
EP_TOKEN_TIME = None

ep_store_id = os.getenv('EP_STORE_ID')
ep_client_id = os.getenv('EP_CLIENT_ID')
ep_client_secret = os.getenv('EP_CLIENT_SECRET')


def get_access_token():
	global EP_ACCESS_TOKEN
	global EP_TOKEN_TIME

	if not EP_ACCESS_TOKEN or datetime.now() > EP_TOKEN_TIME + timedelta(minutes=59):
		data = {
			'client_id': ep_client_id,
			'client_secret': ep_client_secret,
			'grant_type': 'client_credentials',
		}

		response = requests.post('https://api.moltin.com/oauth/access_token', data=data)
		response.raise_for_status()
		EP_ACCESS_TOKEN = response.json()['access_token']
		EP_TOKEN_TIME = datetime.now()
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


def delete_cart_item(bot, query):
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


def download_product_picture(product_image_id):
	headers = {
		'Authorization': get_access_token(),
	}
	image_response = requests.get(f'https://api.moltin.com/v2/files/{product_image_id}', headers=headers)
	image_response.raise_for_status()

	image_url = image_response.json()['data']['link']['href']

	if not os.path.exists(f'pictures/{product_image_id}.jpeg'):
		with open(f'pictures/{product_image_id}.jpeg', 'wb') as f:
			f.write(requests.get(image_url).content)


def add_product_to_shop(product_name, product_sku, product_description, product_price):
	headers = {
		'Authorization': get_access_token(),
	}

	json_data = {
		'data': {
			'type': 'product',
			'name': product_name,
			'slug': f'pizza-{product_sku}',
			'sku': f'{product_sku}',
			'description': product_description,
			'manage_stock': False,
			'price': [
				{
					'amount': product_price,
					'currency': 'RUB',
					'includes_tax': True,
				},
			],
			'status': 'live',
			'commodity_type': 'physical',
		},
	}

	response = requests.post('https://api.moltin.com/v2/products', headers=headers, json=json_data)
	response.raise_for_status()
	return response.json()

def upload_picture(file_url):
	headers = {
		'Authorization': get_access_token(),
	}

	files = {
		'file_location': (None, file_url),
	}

	response = requests.post('https://api.moltin.com/v2/files', headers=headers, files=files)
	response.raise_for_status()
	return response.json()


def link_picture_with_product(image_id, product_id):
	headers = {
		'Authorization': get_access_token(),
	}

	json_data = {
		'data': {
			'type': 'main_image',
			'id': image_id,
		},
	}

	response = requests.post(f'https://api.moltin.com/v2/products/{product_id}/relationships/main-image',
	                         headers=headers,
	                         json=json_data)
	response.raise_for_status()
	return response.json()


def create_flow(name, slug, description, enabled):
	headers = {
		'Authorization': get_access_token(),
	}

	json_data = {
		'data': {
			'type': 'flow',
			'name': name,
			'slug': slug,
			'description': description,
			'enabled': enabled,
		},
	}

	response = requests.post('https://api.moltin.com/v2/flows', headers=headers, json=json_data)
	response.raise_for_status()
	return response.json()


def create_field(name, slug, description, flow_id):
	headers = {
		'Authorization': get_access_token(),
		}

	json_data = {
		'data': {
			'type': 'field',
			'name': name,
			'slug': slug,
			'field_type': 'string',
			'description': description,
			'required': False,
			'enabled': True,
			'relationships': {
				'flow': {
					'data': {
						'type': 'flow',
						'id': flow_id,
					},
				},
			},
		},
	}

	response = requests.post('https://api.moltin.com/v2/fields', headers=headers, json=json_data)
	response.raise_for_status()
	return response.json()


def create_entry(flow_slug, address, alias, longitude, latitude):
	headers = {
		'Authorization': f'Bearer {get_access_token()}',
		'Content-Type': 'application/json',
	}

	json_data = {
		'data': {
			'type': 'entry',
			'Address': address,
			'Alias': alias,
			'Longitude': longitude,
			'Latitude': latitude,
		},
	}

	response = requests.post(f'https://api.moltin.com/v2/flows/{flow_slug}/entries',
	                         headers=headers, json=json_data)
	response.raise_for_status()


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


def update_field(field_id, field_name):
	headers = {
		'Authorization': get_access_token(),
		'Content-Type': 'application/json',
	}

	data = {
		'data': {
			'id': field_name,
			'type': 'field',
			'name': '2079105051'
		},
	}

	response = requests.post(f'https://api.moltin.com/v2/fields/{field_id}', headers=headers, json=data)
	response.raise_for_status()
	return response.json()


def get_all_fields():
	headers = {
		'Authorization': get_access_token(),
	}

	response = requests.get('https://api.moltin.com/v2/fields', headers=headers)
	response.raise_for_status()
	return response.json()


def update_entry(flow_slug, entry_id, field_name, courier_id):
	headers = {
		'Authorization': get_access_token(),
		'Content-Type': 'application/json',
	}

	data = {
		'data': {
			'id': entry_id,
			'type': 'entry',
			field_name: courier_id
		},
	}

	response = requests.put(f'https://api.moltin.com/v2/flows/{flow_slug}/entries/{entry_id}', headers=headers, json=data)
	response.raise_for_status()
	return response.json()


def update_field_in_flow(slug):
	all_entries = get_all_entries(slug)

	for entry in all_entries['data']:
		entry_id = entry['id']

		update_entry('Pizzeria', entry_id, 'courierID', '2079105051')


def get_restaurant_list():
	url = 'https://dvmn.org/media/filer_public/90/90/9090ecbf-249f-42c7-8635-a96985268b88/addresses.json'
	addresses_list = requests.get(url)
	addresses_list.raise_for_status()
	return addresses_list.json()


def get_pizzas_list():
	url = 'https://dvmn.org/media/filer_public/a2/5a/a25a7cbd-541c-4caf-9bf9-70dcdf4a592e/menu.json'
	pizzas_list = requests.get(url)
	pizzas_list.raise_for_status()
	return pizzas_list.json()


def upload_product_to_motlin():
	pizzas_list = get_pizzas_list()

	for pizza in pizzas_list:
		product_sku = pizza['id']
		product_name = pizza['name']
		product_description = pizza['description']
		product_price = pizza['price']
		product_image_url = pizza['product_image']['url']

		product_info = add_product_to_shop(product_name, product_sku,
		                                   product_description, product_price)
		product_id = product_info['data']['id']

		image_info = upload_picture(product_image_url)
		image_id = image_info['data']['id']

		link_picture_with_product(image_id, product_id)


def add_fields_to_flow():
	#TODO поправить вызов функции в зависиммости от вызова

	# flow_info = create_flow('Clients', 'Clients_Addresses', 'Clients_Addresses', True)
	flow_id_pizzeria = '9af1050e-1133-4fcb-963d-6afe5a5f2eee'
	# flow_id_client = 'a064cdac-052d-4244-84aa-a0574e7d2429'
	# flow_id = flow_info['data']['id']

	fields = ['courierID']

	for field in fields:
		create_field(field, field, field, flow_id_pizzeria)


def add_record_to_flow(flow_name='Pizzeria'):
	# flow name 'Pizzeria' or 'Clients'
	restaurant_list = get_restaurant_list()

	for restaurant in restaurant_list:
		address = restaurant['address']['full']
		alias = restaurant['alias']
		latitude = restaurant['coordinates']['lat']
		longitude = restaurant['coordinates']['lon']
		create_entry(flow_name, address, alias, longitude, latitude)
