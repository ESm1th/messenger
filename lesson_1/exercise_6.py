import chardet


# по умолчанию у файла кодировка 'utf-8'

file = 'test_file.txt'


def file_opener(path):
    with open(path, 'r') as f:
        print('File encoding: ', chardet.detect(f.read().encode())['encoding'])
    with open(path, 'r', encoding='utf-8') as f:
        print(f.read().strip())


if __name__ == '__main__':
    file_opener(file)
