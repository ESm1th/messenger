given_strings = [
    'разработка',
    'администрирование',
    'protocol',
    'standard'
]


def translator(sequence):
    for var in sequence:
        var = var.encode()
        print(var, var.decode())


if __name__ == '__main__':
    translator(given_strings)
