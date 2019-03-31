import chardet


rus_list = [
    'разработка',
    'сокет',
    'декоратор'
]

unicode_list = [
    '\u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0430',
    '\u0441\u043e\u043a\u0435\u0442',
    '\u0434\u0435\u043a\u043e\u0440\u0430\u0442\u043e\u0440'
]


def check(sequence):
    for var in sequence:
        print(type(var), var, chardet.detect(var.encode())['encoding'])


if __name__ == '__main__':
    check(rus_list)
    check(unicode_list)
    print(rus_list == unicode_list)
