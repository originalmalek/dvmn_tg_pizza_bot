from motlin_api import get_products, get_image_url, get_products_by_category
from dotenv import load_dotenv


def create_product_carousel(category_name='main'):
    product_carousel = []
    products = get_products_by_category(category_name)

    for product in products['data']:
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


def create_last_page_of_carousel(category_name):
    all_pizza_categories = {'main': 'Основные пиццы',
                            'special': 'Особенные пиццы',
                            'hot': 'Острые пиццы',
                            'rich': 'Сытные пиццы',
                            }
    all_pizza_categories.pop(category_name)
    pizzas_categories_values = list(all_pizza_categories.items())


    return [{
        'title': f'Не нашли нужную пиццу?',
        'image_url': 'https://primepizza.ru/uploads/position/large_0c07c6fd5c4dcadddaf4a2f1a2c218760b20c396.jpg',
        'subtitle': f'Найдите свою пиццу в другой категории',
        'buttons': [
            {
                'type': 'postback',
                'title': pizzas_categories_values[0][1],
                'payload': pizzas_categories_values[0][0],
            },
            {
                'type': 'postback',
                'title': pizzas_categories_values[1][1],
                'payload': pizzas_categories_values[1][0],
            },
            {
                'type': 'postback',
                'title': pizzas_categories_values[2][1],
                'payload': pizzas_categories_values[2][0],
            },
        ],
    }]


if __name__ == '__main__':
    load_dotenv()
