import subprocess


resources = [
    'yandex.ru',
    'youtube.com'
]


def pinger(sequence):
    for resource in sequence:
        ping = subprocess.Popen(['ping', resource], stdout=subprocess.PIPE)
        for line in ping.stdout:
            print(line.decode('cp1251').encode('utf-8').decode('utf-8'))


if __name__ == '__main__':
    pinger(resources)
