# convert 'main_data.csv' to 'yaml'

import csv
import yaml


file_path = 'main_data.csv'


def from_csv_to_yaml(path):
    csv_list = []

    with open(path, encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            csv_list.append(dict(row))

    with open('from_csv_to_yaml.yaml', 'w', encoding='utf-8') as file:
        yaml.dump(csv_list, file, default_flow_style=False, allow_unicode=True)


if __name__ == '__main__':
    from_csv_to_yaml(file_path)
