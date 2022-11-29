from motlin_api import get_products
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def generate_menu_markup(page_number=1):
	products = get_products()
	pagination_keyboard = []
	pages_quantity = len(products['data']) // 8 + 1

	num_last_product = page_number * 8
	num_first_product = num_last_product - 8

	markup = [([InlineKeyboardButton(product['name'],
	                                 callback_data=product['id'])]) for product in
	          products['data'][num_first_product:num_last_product]]
	markup.append([InlineKeyboardButton('Корзина 🛒', callback_data='cart')])
	for page in range(0,pages_quantity):
		callback_data = str({"act": "page", "page_num": f"{page + 1}"}).replace("'", '"')

		pagination_keyboard.append(InlineKeyboardButton(f"{page + 1}", callback_data=callback_data))

	markup.append(pagination_keyboard)
	return markup


def generate_product_markup(product_sku):
	back_button = [InlineKeyboardButton("Back", callback_data='{"action": "go_back"}')]
	add_to_cart_keyboard = []

	callback_data = str({"action": "add_to_cart", "sku": product_sku, "quantity": 1}).replace("'", '"')
	add_to_cart_keyboard.append(InlineKeyboardButton(f"Добавить в корзину",
	                                                 callback_data=callback_data))

	keyboard = [[InlineKeyboardButton('Корзина 🛒', callback_data='cart')],
	            add_to_cart_keyboard, back_button]

	return InlineKeyboardMarkup(keyboard)


def generate_cart_markup(cart):
	delete_from_cart_keyboard = []

	for product in cart['data']:
		product_name = product['name']
		product_id = product['id']

		callback_data = str({"action": "del", "id": f"{product_id}"}).replace("'", '"')

		delete_from_cart_keyboard.append([InlineKeyboardButton(f"Удалить {product_name}", callback_data=callback_data)])

	back_button = [InlineKeyboardButton("Back", callback_data='{"action": "go_back"}')]
	pay_button = [InlineKeyboardButton("Заказать", callback_data='{"action": "order"}')]
	delete_from_cart_keyboard.append(back_button)
	delete_from_cart_keyboard.append(pay_button)
	keyboard = delete_from_cart_keyboard
	return InlineKeyboardMarkup(keyboard)


def generate_delivery_markup():
    keyboard = [[InlineKeyboardButton("Доставка", callback_data='delivery')],
	            [InlineKeyboardButton("Самовывоз", callback_data='pickup')]]

	return InlineKeyboardMarkup(keyboard)

	return InlineKeyboardMarkup(keyboard)
