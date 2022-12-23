from motlin_api import get_image_url, get_products_by_category, get_cart
from dotenv import load_dotenv


def create_product_carousel(category_name='main'):
    product_carousel = []
    products = get_products_by_category(category_name)

    for product in products['data']:
        product_id = product['sku']
        product_name = product['name']
        product_description = product['description']
        product_price = product['meta']['display_price']['with_tax']['amount']
        product_image_id = product['relationships']['main_image']['data']['id']
        image_url = get_image_url(product_image_id)

        product_carousel.append({
            'title': f'{product_name}. {product_price} руб',
            'image_url': f'{image_url}',
            'subtitle': f'{product_description}',
            'buttons': [
                {
                    'type': 'postback',
                    'title': 'Добавить корзину',
                    'payload': str({'add_to_cart': product_id}),
                },
            ],
        })
    return product_carousel


def create_first_templates_of_menu():
    return [{
        'title': f'Пиццерия. Заказать пиццу прямо сейчас.',
        'image_url': 'https://st2.depositphotos.com/3687485/9049/v/950/depositphotos_90493674-stock-illustration-pizza-flat-icon-logo-template.jpg',
        'subtitle': f'Быcтрая доставка за 35 минут',
        'buttons': [
            {
                'type': 'postback',
                'title': 'Корзина',
                'payload': 'cart',
            },
            {
                'type': 'postback',
                'title': 'Сделать заказ',
                'payload': 'make_order',
            },
        ],
    }]


def create_last_template_of_menu(category_name):
    pizza_categories_in_menu = []
    all_pizza_categories = {'main': 'Основные пиццы',
                            'special': 'Особенные пиццы',
                            'hot': 'Острые пиццы',
                            'rich': 'Сытные пиццы',
                            }
    all_pizza_categories.pop(category_name)
    for key, value in all_pizza_categories.items():
        pizza_categories_in_menu.append({
            'type': 'postback',
            'title': value,
            'payload': key,
        })

    return [{
        'title': f'Не нашли нужную пиццу?',
        'image_url': 'https://primepizza.ru/uploads/position/large_0c07c6fd5c4dcadddaf4a2f1a2c218760b20c396.jpg',
        'subtitle': f'Найдите свою пиццу в другой категории',
        'buttons': pizza_categories_in_menu
        ,
    }]


def create_product_templates_of_cart(cart):
    cart_carousel = []
    for product in cart['data']:
        product_id = product['id']
        product_sku = product['sku']
        product_name = product['name']
        product_description = product['description']
        image_url = product['image']['href']
        quantity = product['quantity']
        total_amount = product['value']['amount']


        cart_carousel.append({
            'title': f'{product_name}. {quantity} пиццы в корзине на {total_amount} руб.',
            'image_url': f'{image_url}',
            'subtitle': f'{product_description}',
            'buttons': [
                {
                    'type': 'postback',
                    'title': 'Добавить ещё одну',
                    'payload': str({'add_to_cart': product_sku}),
                },
                {
                    'type': 'postback',
                    'title': 'Удалить из корзины',
                    'payload': str({'del_from_cart': product_id}),
                },
            ],
        })
    return cart_carousel


def create_first_templates_of_cart(money_amount):
    return [{
        'title': f'Ваш заказ на {money_amount} рублей',
        'image_url': 'https://st2.depositphotos.com/3687485/9049/v/950/depositphotos_90493674-stock-illustration-pizza-flat-icon-logo-template.jpg',
        'subtitle': f'Быcтрая доставка за 35 минут',
        'buttons': [
            {
                'type': 'postback',
                'title': 'Возврат в меню',
                'payload': 'menu',
            },
        ],
    }]


if __name__ == '__main__':
    load_dotenv()
