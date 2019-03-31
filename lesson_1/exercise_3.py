given_strings = [
    'attribute',
    'класс',
    'функция',
    'type'
]


def check(sequence):
    print('This words cannot be written in byte type:')
    for var in sequence:
        if not var.isascii():
            print(var)


if __name__ == '__main__':
    check(given_strings)
