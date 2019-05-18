import subprocess
import ipaddress
import re

pattern = r'^\d+.\d+.\d+.\d+$'


def host_ping(hosts):
    for host in hosts:
        if re.search(pattern, host):
            host = ipaddress.ip_address(host)

        process = subprocess.Popen(
            ['ping', '-c', '3', str(host)],
            stdout=subprocess.PIPE
        )
        process.communicate()
        if process.returncode == 0:
            print(f'Адресс: {host} доступен')
        else:
            print(f'Адресс: {host} недоступен')


hosts = [
    '222.222.222.222',
    '127.0.0.1',
    '0.0.0.0',
    '192.168.0.1',
    'localhost',
    'google.com',
    'yandex.ru'
]


host_ping(hosts)
