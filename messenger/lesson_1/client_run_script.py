import os

# Работает в 'ubuntu', так как используется запуск программ
# в фоновом режиме с помощью оператора '&'


def run_client_app():

    num = input('Введите нжное количество для запуска: ')
    dir_path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(os.path.dirname(dir_path), 'client/')

    for n in range(int(num)):
        os.system(f'python {path} &')


run_client_app()
