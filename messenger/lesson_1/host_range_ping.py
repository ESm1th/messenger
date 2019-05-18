import subprocess


def host_range_ping(start_host, end_host):
    start = start_host.split('.')[-1]
    end = end_host.split('.')[-1]
    basic_address = '.'.join(start_host.split('.')[:3])

    for i in range(int(start), int(end) + 1):
        host = '.'.join([basic_address, str(i)])
        process = subprocess.Popen(
            ['ping', '-c', '3', str(host)],
            stdout=subprocess.PIPE
        )
        process.communicate()

        if process.returncode == 0:
            print(f'Адресс: {host} доступен')
        else:
            print(f'Адресс: {host} недоступен')


host_range_ping('134.0.112.131', '134.0.112.140')
