from pathlib import Path
from setuptools import setup

from anicli_ru import __version__

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()
setup(
    name='anicli-ru',
    version=__version__,
    packages=['anicli_ru'],
    url='https://github.com/vypivshiy/ani-cli-ru',
    license='GPL-3',
    author='georgiy',
    author_email='',
    python_requires='>=3.6',
    description='anime-ru grabber video api',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=['requests'],
)
