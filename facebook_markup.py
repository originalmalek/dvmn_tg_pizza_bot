from motlin_api import get_products, get_image_url
from dotenv import load_dotenv

def create_product_carousel():
	product_carousel = []
	products = get_products()
	for product in products['data'][0:5]:
		product_id = product['id']
		product_name = product['name']
		product_description = product['description']
		product_price = product['meta']['display_price']['with_tax']['amount']
		product_image_id = product['relationships']['main_image']['data']['id']
		image_url = get_image_url(product_image_id)
		product_carousel.append({
			'title': f'{product_name}. {product_price} руб',
			'image_url': f'{image_url}',
			'subtitle': f'{product_description}',
			'default_action': {
				'type': 'web_url',
				'url': 'https://www.originalcoastclothing.com/',
				'webview_height_ratio': 'tall',
			},
			'buttons': [
				{
					'type': 'postback',
					'title': 'Корзина',
					'payload': 'cart',
				},
				{
					'type': 'postback',
					'title': 'Добавить корзину',
					'payload': product_id,
				},
			],
		})
	return product_carousel


def create_first_page_of_carousel():
	return [{
			'title': f'Пиццерия. Заказать пиццу прямо сейчас.',
			'image_url': f'https://st2.depositphotos.com/3687485/9049/v/950/depositphotos_90493674-stock-illustration-pizza-flat-icon-logo-template.jpg',
			'subtitle': f'Быcтрая доставка за 35 минут',
			'default_action': {
				'type': 'web_url',
				'url': 'https://www.originalcoastclothing.com/',
				'webview_height_ratio': 'tall',
			},
			'buttons': [
				{
					'type': 'postback',
					'title': 'Корзина',
					'payload': 'cart',
				},
				{
					'type': 'postback',
					'title': 'Акции',
					'payload': 'sale',
				},
				{
					'type': 'postback',
					'title': 'Сделать заказ',
					'payload': 'make_order',
				},
			],
		}]




if __name__ == '__main__':
	load_dotenv()
