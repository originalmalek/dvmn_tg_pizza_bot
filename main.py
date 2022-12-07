import json
import logging
import os

import redis
import requests

from geopy import distance
from textwrap import dedent
from dotenv import load_dotenv
from telegram_logger import MyLogsHandler

from telegram_markup import generate_menu_markup, generate_product_markup, generate_cart_markup, \
	

from telegram import InlineKeyboardMarkup, LabeledPrice, InlineKeyboardButton

from telegram.ext import Filters, Updater, CallbackQueryHandler, CommandHandler, \
	MessageHandler, PreCheckoutQueryHandler

from motlin_api import get_cart, add_item_to_cart, get_product_data, delete_cart_item, \
	download_product_picture, get_all_entries, create_entry_client_address


logger = logging.getLogger('TG ElasticPath Bot')


def get_database_connection():
	global _database
	if _database is None:
		database_password = os.getenv('DATABASE_PASSWORD')
		database_host = os.getenv('DATABASE_HOST')
		database_port = os.getenv('DATABASE_PORT')
		_database = redis.Redis(host=database_host, port=database_port, password=database_password)
	return _database


def handle_description(bot, update, job_queue):
	query = update.callback_query

	if query.data == 'cart':
		send_user_cart(bot, query)
		return 'HANDLE_CART'

	if json.loads(query.data)['action'] == 'go_back':
		reply_markup = InlineKeyboardMarkup(generate_menu_markup(page_number=1))

		bot.send_message(text='Please choose product:', chat_id=query.message.chat_id,
		                 reply_markup=reply_markup)

		bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

		return 'HANDLE_MENU'

	if json.loads(query.data)['action'] == 'add_to_cart':
		product_sku = json.loads(query.data)['sku']
		quantity = json.loads(query.data)['quantity']
		add_item_to_cart(product_sku, quantity, query.message.chat_id)
		bot.answer_callback_query(update.callback_query.id, text="Пицца добавлена к корзину",
		                          show_alert=True)

		return 'HANDLE_DESCRIPTION'


def handle_users_reply(bot, update, job_queue):
	db = get_database_connection()
	if update.message:
		user_reply = update.message.text
		chat_id = update.message.chat_id
	elif update.callback_query:
		user_reply = update.callback_query.data
		chat_id = update.callback_query.message.chat_id
	else:
		return
	if user_reply == '/start':
		user_state = 'START'
	else:
		user_state = db.get(chat_id).decode('utf-8')

	states_functions = {
		'START': start,
		'HANDLE_MENU': handle_menu,
		'HANDLE_DESCRIPTION': handle_description,
		'HANDLE_CART': handle_cart,
		'HANDLE_LOCATION': handle_location,
		'HANDLE_PICKUP_DELIVERY': handle_pickup_delivery

	}
	state_handler = states_functions[user_state]

	try:
		next_state = state_handler(bot, update, job_queue)
		db.set(chat_id, next_state)
	except Exception as err:
		logger.error(err)


def start(bot, update, job_queue):
	reply_markup = InlineKeyboardMarkup(generate_menu_markup())
	update.message.reply_text('Please choose product:', reply_markup=reply_markup)
	return 'HANDLE_MENU'


def handle_cart(bot, update, job_queue):
	query = update.callback_query

	if json.loads(query.data)['action'] == 'go_back':
		reply_markup = InlineKeyboardMarkup(generate_menu_markup(page_number=1))

		bot.send_message(text='Please choose product:', chat_id=query.message.chat_id,
		                 reply_markup=reply_markup)

		bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

		return 'HANDLE_MENU'

	if json.loads(query.data)['action'] == 'order':
		bot.send_message(text='Введите ваш адрес или пришлите свою геопозицию:',
		                 chat_id=query.message.chat_id, )

		bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

		return 'HANDLE_LOCATION'

	if json.loads(query.data)['action'] == 'del':
		delete_cart_item(query)
		send_user_cart(bot, query)
		return 'HANDLE_CART'


def get_user_order(cart):
	user_order = ''

	for product in cart['data']:
		product_name = product['name']
		product_description = product['description']
		product_quantity = product['quantity']
		product_total_price = product['meta']['display_price']['with_tax']['value']['formatted']

		user_order += dedent(f'''{product_name}
								 {product_description}
	                             {product_quantity} шт. за {product_total_price}\n\n''')

	total_price = cart['meta']['display_price']['with_tax']['formatted']
	user_order += f'Total price: {total_price}'
	return user_order


def send_user_cart(bot, query):
	chat_id = query.message.chat_id
	cart = get_cart(chat_id)
	user_order = get_user_order(cart)

	reply_markup = generate_cart_markup(cart)

	bot.send_message(text=user_order, chat_id=chat_id, reply_markup=reply_markup)
	bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

	return 'HANDLE_CART'


def handle_menu(bot, update, job_queue):
	query = update.callback_query
	try:
		if json.loads(query.data)['act'] in query.data:
			page_number = int(json.loads(query.data)['page_num'])

			reply_markup = InlineKeyboardMarkup(generate_menu_markup(page_number=page_number))

			bot.send_message(text='Please choose product:', chat_id=query.message.chat_id,
			                 reply_markup=reply_markup)
			bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
			return 'HANDLE_MENU'
	except:
		pass
	if query.data == 'cart':
		send_user_cart(bot, query)
		return 'HANDLE_CART'
	else:
		product_response = get_product_data(query)
		product_sku = product_response['sku']
		product_name = product_response['name']
		product_description = product_response['description']
		product_price = product_response['meta']['display_price']['with_tax']['formatted']
		product_image_id = product_response['relationships']['main_image']['data']['id']

		download_product_picture(product_image_id)

		reply_markup = generate_product_markup(product_sku)

		caption = dedent(f'''Описание продукта:

						{product_name}

						{product_description}

                         Стоимость: {product_price} руб. за 1 пиццу''')

		with open(f'pictures/{product_image_id}.jpeg', 'rb') as photo:
			bot.send_photo(caption=caption,
			               chat_id=query.message.chat_id,
			               photo=photo,
			               reply_markup=reply_markup,
			               )

		bot.delete_message(chat_id=query.message.chat_id,
		                   message_id=query.message.message_id)

		return 'HANDLE_DESCRIPTION'


def fetch_coordinates(address):
	base_url = "https://geocode-maps.yandex.ru/1.x"
	response = requests.get(base_url, params={
		"geocode": address,
		"apikey": yandex_api_key,
		"format": "json",
	})
	response.raise_for_status()
	found_places = response.json()['response']['GeoObjectCollection']['featureMember']

	if not found_places:
		return None

	most_relevant = found_places[0]
	lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
	return lat, lon


def handle_location(bot, update, job_queue):
	message = None
	if update.message.text:
		current_pos = fetch_coordinates(update.message.text)
	elif update.edited_message:
		message = update.edited_message
	else:
		message = update.message
		current_pos = (message.location.latitude, message.location.longitude)

	if current_pos is None:
		bot.send_message(text='''Не могу распознать адрес.
		                      Введите ваш адрес или пришлите свою геопозицию: заново''',
		                 chat_id=update.message.chat_id, )

		bot.delete_message(chat_id=update.message.chat_id,
		                   message_id=update.message.message_id)
		return 'HANDLE_LOCATION'

	closest_store = get_closest_store(current_pos)
	km_distance = closest_store['distance']

	create_entry_client_address('Clients_Addresses', update.message.chat_id, current_pos[1], current_pos[0])
	if km_distance <= 0.5:
		reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Доставка", callback_data='delivery')],
	                                        [InlineKeyboardButton("Самовывоз", callback_data='pickup')]])
		bot.send_message(
			text=f'Самовывоз с {closest_store["Address"]} всего {km_distance} км. от вас или бесплатная доставка',
			chat_id=update.message.chat_id,
			reply_markup=reply_markup)

		bot.delete_message(chat_id=update.message.chat_id,
		                   message_id=update.message.message_id)
		return 'HANDLE_PICKUP_DELIVERY'

	if 0.5 < km_distance <= 5:
		bot.send_message(text=f'Доставка 100 руб',
		                 chat_id=update.message.chat_id, )

		bot.delete_message(chat_id=update.message.chat_id,
		                   message_id=update.message.message_id)
	if 5 < km_distance <= 20:
		bot.send_message(text=f'Доставка 300 руб',
		                 chat_id=update.message.chat_id, )

		bot.delete_message(chat_id=update.message.chat_id,
		                   message_id=update.message.message_id)
	if 20 < km_distance:
		bot.send_message(text=f'Все пиццерии находятся слишком далеко',
		                 chat_id=update.message.chat_id, )

		bot.delete_message(chat_id=update.message.chat_id,
		                   message_id=update.message.message_id)
	return 'HANDLE_LOCATION'


def get_closest_store(person_location):
	all_entries = get_all_entries('Pizzeria')

	for entry in all_entries['data']:
		km_distance = distance.distance(person_location, (entry['Latitude'], entry['Longitude'])).km
		entry['distance'] = round(km_distance, 2)

	min_distance_entry = min(all_entries['data'], key=lambda x: x['distance'])

	return min_distance_entry


def send_feedback_form(bot, job):
	bot.send_message(chat_id=job.context, text='''Приятного аппетита! *место для рекламы*
												*сообщение что делать если пицца не пришла*''')


def get_user_payment(bot, update, total_price):
	chat_id = update.callback_query.message.chat_id
	title = "Оплата заказа"
	description = "Для завершения, оплатите ваш заказ"

	payload = "Custom-Payload"

	provider_token = telegram_payment_token
	start_parameter = "test-payment"
	currency = "RUB"

	price = total_price

	prices = [LabeledPrice("Оплата заказа", price * 100)]

	bot.sendInvoice(chat_id, title, description, payload,
	                provider_token, start_parameter, currency, prices)


def handle_pickup_delivery(bot, update, job_queue):
	query = update.callback_query
	all_clients_entries = get_all_entries('Clients_Addresses')
	for entry in all_clients_entries['data']:
		if entry['UserId'] == str(query.message.chat_id):
			longitude = entry['Longitude']
			latitude = entry['Latitude']
			break
	closest_store = get_closest_store((latitude, longitude))

	cart = get_cart(query.message.chat_id)

	if query.data == 'delivery':
		user_order = get_user_order(cart)

		bot.send_message(text=user_order,
		                 chat_id=query.message.chat_id, )
		bot.send_location(chat_id=closest_store['courierID'], latitude=latitude, longitude=longitude)

		bot.send_message(text="Ваш заказ принят. Его доставят в течении 60 минут",
		                 chat_id=query.message.chat_id, )

		bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

	if query.data == 'pickup':
		bot.send_message(text=f"Заберите ваш заказ по адресу: {closest_store['Address']}",
		                 chat_id=query.message.chat_id, )

		bot.delete_message(chat_id=query.message.chat_id,
		                   message_id=query.message.message_id)

	total_price = int(cart['meta']['display_price']['with_tax']['amount'])

	get_user_payment(bot, update, total_price)

	queue_job.run_once(send_feedback_form, 3600, context=query.message.chat_id)

	return 'START'


def successful_payment_callback(bot, update):
	update.message.reply_text("Ваш заказ успешно оплачен!")


def precheckout_callback(bot, update):
	query = update.pre_checkout_query
	if query.invoice_payload != 'Custom-Payload':
		bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=False,
		                              error_message="Something went wrong...")
	else:
		bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)


if __name__ == '__main__':
	load_dotenv()
	_database = None
	telegram_api_key = os.getenv('TELEGRAM_API_KEY')
	telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
	yandex_api_key = os.getenv('YANDEX_API_KEY')
	telegram_payment_token = os.getenv('TELEGRAM_PAYMENT_TOKEN')

	my_log_handler = MyLogsHandler(level=logging.DEBUG, telegram_token=telegram_api_key,
	                               chat_id=telegram_chat_id)
	logging.basicConfig(level=20)
	logger.addHandler(my_log_handler)

	updater = Updater(telegram_api_key)
	queue_job = updater.job_queue
	dispatcher = updater.dispatcher

	dispatcher.add_handler(PreCheckoutQueryHandler(precheckout_callback))
	dispatcher.add_handler(MessageHandler(Filters.successful_payment, successful_payment_callback))
	location_handler = MessageHandler(Filters.location, handle_users_reply, pass_job_queue=True)
	dispatcher.add_handler(location_handler)
	dispatcher.add_handler(CallbackQueryHandler(handle_users_reply, pass_job_queue=True))
	dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply, pass_job_queue=True))
	dispatcher.add_handler(CommandHandler('start', handle_users_reply, pass_job_queue=True))

	try:
		logger.warning('Bot TG is working')
		updater.start_polling()
	except Exception as err:
		logger.exception('Bot TG got an error')
