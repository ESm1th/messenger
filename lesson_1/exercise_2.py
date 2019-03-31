import chardet


bytes_list = [
    b'class',
    b'function',
    b'method'
]


def check(sequence):
    for var in sequence:
        print(
            type(var),
            var,
            'length={}'.format(len(var)),
            chardet.detect(var)['encoding']
        )


if __name__ == '__main__':
    check(bytes_list)
