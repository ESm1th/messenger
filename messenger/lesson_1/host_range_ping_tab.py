from tabulate import tabulate
import subprocess


def host_range_ping_tab(start_host, end_host):
    start = start_host.split('.')[-1]
    end = end_host.split('.')[-1]
    basic_address = '.'.join(start_host.split('.')[:3])

    reachable = []
    unreachable = []

    for i in range(int(start), int(end) + 1):
        host = '.'.join([basic_address, str(i)])
        process = subprocess.Popen(
            ['ping', '-c', '3', str(host)],
            stdout=subprocess.PIPE
        )
        process.communicate()

        if process.returncode == 0:
            reachable.append(host)
        else:
            unreachable.append(host)

    print(
        tabulate(
            zip(reachable, unreachable),
            headers=['Reachable', 'Unreachable'],
            tablefmt='grid'
        )
    )


host_range_ping_tab('134.0.112.131', '134.0.112.140')