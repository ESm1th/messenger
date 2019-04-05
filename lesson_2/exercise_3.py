import yaml


def write_to_yaml(client_id, products, price):
    """
    Write data to 'yaml' file.
    Default currency for price - 'euro'.
    """
    order = {
        'products': products,
        'client id': client_id,
        'prices': {
            'euro': '{0} €'.format(price),
            'pound': '{0} £'.format(round(price * 0.857)),
            'yean': '{0} ¥'.format(round(price * 125.44))
        }
    }

    with open('order.yaml', 'w', encoding='utf-8') as file:
        yaml.dump(order, file, default_flow_style=False, allow_unicode=True)

    with open('order.yaml', encoding='utf-8') as file:
        print(file.read())


if __name__ == '__main__':
    write_to_yaml(12, ['ps4', 'x-box', 'nintendo 64'], 2500)
