from setuptools import setup, find_packages


with open('requirements.txt') as file:
    requirements = [
        line.strip() for line in file.readlines()
    ]


setup(
    name='server',
    version='1.0',
    description='Simple messengers server',
    author='Evgeniy Kuznetsov',
    author_email='evgeny@gmail.com',
    packages=find_packages(),
    install_requires=requirements
)