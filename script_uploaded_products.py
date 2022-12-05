import requests
from motlin_api import get_access_token


def get_pizzas_list():
	url = 'https://dvmn.org/media/filer_public/a2/5a/a25a7cbd-541c-4caf-9bf9-70dcdf4a592e/menu.json'
	pizzas_list = requests.get(url)
	pizzas_list.raise_for_status()
	return pizzas_list.json()


def add_product_to_shop(product_name, product_sku, product_description, product_price):
	headers = {
		'Authorization': get_access_token(),
		'Content-Type': 'application/json'
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
	if response.status_code == 409:         #check if product exists in catalog
		return 'product_uploaded'
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


def upload_products_to_motlin():
	pizzas_list = get_pizzas_list()

	for pizza in pizzas_list:
		product_sku = pizza['id']
		product_name = pizza['name']
		product_description = pizza['description']
		product_price = pizza['price']
		product_image_url = pizza['product_image']['url']

		product_info = add_product_to_shop(product_name, product_sku,
		                                   product_description, product_price)

		if product_info == 'product_uploaded':
			continue
		product_id = product_info['data']['id']

		image_info = upload_picture(product_image_url)
		image_id = image_info['data']['id']

		link_picture_with_product(image_id, product_id)


if __name__ == '__main__':
	upload_products_to_motlin()
