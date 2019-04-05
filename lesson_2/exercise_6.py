# convert 'orders.json' to 'yaml'

import json
import yaml


file_path = 'orders.json'


def from_json_to_yaml(path):
    with open(path, encoding='utf-8') as file:
        json_data = json.load(file)

    with open('from_json_to_yaml.yaml', 'w', encoding='utf-8') as file:
        yaml.dump(
            json_data, file, default_flow_style=False,
            allow_unicode=True, indent=4
        )


if __name__ == '__main__':
    from_json_to_yaml(file_path)
