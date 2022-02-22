from setuptools import setup, find_packages
from anicli_ru.__version__ import __version__

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='anicli-ru',
    version=__version__,
    packages=find_packages(),
    url='https://github.com/vypivshiy/ani-cli-ru',
    license='GPL-3',
    author='Georgiy aka Vypivshiy',
    author_email='',
    python_requires='>=3.7',
    description='anime grabber video api and cli tool',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=['requests'],
    entry_points={
        'console_scripts': ['anicli-ru = anicli_ru.anicli:main'],
    }
)
