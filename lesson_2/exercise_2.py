import json


def write_orders_to_json(
        item, quantity, price, buyer, date):

    data = {
        'item': item,
        'quantity': quantity,
        'price': price,
        'buyer': buyer,
        'date': date
    }

    with open('orders.json', 'r') as file:
        orders_dict = json.load(file)

    orders_dict['orders'].append(data)

    with open('orders.json', 'w') as file:
        json.dump(orders_dict, file, indent=4)


if __name__ == '__main__':
    write_orders_to_json('lamp', 2, 1000, 'Aleksey', '01.04.2019')
