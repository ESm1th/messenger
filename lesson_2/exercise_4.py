# convert 'main_data.csv' to 'json'

import csv
import json


file_path = 'main_data.csv'


def from_csv_to_json(path):
    csv_list = []

    with open(path, encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            csv_list.append(dict(row))

    with open('from_csv_to_json.json', 'w', encoding='utf-8') as file:
        json.dump(csv_list, file, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    from_csv_to_json(file_path)
