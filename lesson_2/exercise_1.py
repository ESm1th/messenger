import re
import glob
import csv
from collections import OrderedDict

data_files = glob.glob('info_*.txt')


def get_data(sequence):
    """
    Get significant data from list of txt files in current directory.
    Files store certain information.
    """
    lists = OrderedDict({
        'os_prod_list': [],
        'os_name_list': [],
        'os_code_list': [],
        'os_type_list': []
    })

    patterns = {
        'manufacturer': r'^Изготовитель системы:\s*([\w\d]+)$',
        'title': r'^Название ОС:\s*([\w\d\s\.]+)$',
        'code': r'^Код продукта:\s*([\w\d\s-]+)$',
        'type': r'^Тип системы:\s*([\w\d\s-]+)$'
    }

    for info_file in sequence:
        with open(info_file) as file:
            for line in file:
                for key, pattern in patterns.items():
                    data = re.search(pattern, line)
                    if data:
                        if key == 'manufacturer':
                            lists['os_prod_list'].append(
                                data.group(1).strip()
                                )
                        elif key == 'title':
                            lists['os_name_list'].append(
                                data.group(1).strip()
                                )
                        elif key == 'code':
                            lists['os_code_list'].append(
                                data.group(1).strip()
                            )
                        else:
                            lists['os_type_list'].append(
                                data.group(1).strip()
                            )
    main_data = [
        [
            'Изготовитель системы',
            'Название ОС',
            'Код продукта',
            'Тип системы'
        ]
    ]

    for i in range(len(main_data[0])-1):
        data = []
        for value in lists.values():
            data.append(value[i])
        main_data.append(data)

    return main_data


def write_csv(filename, files):
    main = get_data(files)
    with open(filename, 'w', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(main)


if __name__ == '__main__':
    write_csv('main_data.csv', data_files)
