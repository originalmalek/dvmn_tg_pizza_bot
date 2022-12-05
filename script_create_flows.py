import os
import requests
from dotenv import load_dotenv
from motlin_api import get_access_token


def create_pizzeria_entry(flow_slug, address, alias, longitude, latitude, courier_id):
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
			'courierID': courier_id
		},
	}

	response = requests.post(f'https://api.moltin.com/v2/flows/{flow_slug}/entries',
	                         headers=headers, json=json_data)
	response.raise_for_status()


def get_restaurant_list():
	url = 'https://dvmn.org/media/filer_public/90/90/9090ecbf-249f-42c7-8635-a96985268b88/addresses.json'
	addresses_list = requests.get(url)
	addresses_list.raise_for_status()
	return addresses_list.json()


def add_record_to_pizzeria_flow(courier_id):
	# flow name 'Pizzeria' or 'Clients'
	restaurant_list = get_restaurant_list()

	for restaurant in restaurant_list:
		address = restaurant['address']['full']
		alias = restaurant['alias']
		latitude = restaurant['coordinates']['lat']
		longitude = restaurant['coordinates']['lon']
		courier_id = courier_id
		create_pizzeria_entry('Pizzeria', address, alias, longitude, latitude, courier_id)


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
	if response.status_code == 422:          #check if flow exist in account
		return 'flow exists'
	response.raise_for_status()
	return response.json()['data']['id']


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


def add_fields_to_pizzeria_flow(pizzeria_flow_id):
	fields = ['Address', 'Alias', 'Longitude', 'Latitude', 'courierID']

	for field in fields:
		create_field(field, field, field, pizzeria_flow_id)


def add_fields_to_clients_flow(clients_flow_id):
	fields = ['UserId', 'Longitude', 'Latitude']

	for field in fields:
		create_field(field, field, field, clients_flow_id)


if __name__ == '__main__':
	load_dotenv()
	courier_id = os.getenv('COURIER_ID')

	clients_flow_id = create_flow('Clients', 'Clients_Addresses', 'Clients_Addresses', True)
	add_fields_to_clients_flow(clients_flow_id)

	pizzeria_flow_id = create_flow('Pizzeria', 'Pizzeria', 'Pizzeria_addresses', True)
	add_fields_to_pizzeria_flow(pizzeria_flow_id)
	add_record_to_pizzeria_flow(courier_id)
