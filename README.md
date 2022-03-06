# anicli-ru
___
Скрипт для поиска и просмотра аниме из терминала с русской озвучкой или субтитрами для linux систем, 
написанный на python.

Парсит видео со сторонних сайтов, **как youtube-dl**.
___
# Supported video hostings:
* sibnet
* aniboom
* kodik
---
# Dependencies:
* python 3.7+
* mpv
* ffmpeg (опционально, для скачивания видео через аргумент "**-d**")
___
# Install:
```
# Если у вас установлен скрипт версией ниже 4.0.0, то перед обновлением удалите старый файл запуска командой:
sudo rm /usr/local/bin/anicli-ru

# установка 
python3 -m pip install anicli-ru

# или клонировать и установить вручную:

git clone https://github.com/vypivshiy/ani-cli-ru && cd ani-cli-ru
pip install .
```
___
# Usage:
`anicli-ru`
___
# CLI Commands:
```
q [q]uit - выход из программы
e [e]xit - alias q
b [b]ack to the previous step - возвратиться на предыдущий шаг
h [h]elp - вывод списка доступных команд
c [c]lear - очистить консоль
o [o]ngoing - напечатать недавно вышедшие онгоинги
```
# FAQ
**Q**: У меня скрипт ничего не находит

**A**: Возможно сайт с которого хотите достать видео включили cloudflare или не работает. 
Используйте сторонние источники через аргумент `-s {число}`. 

Все доступные источники для парсинга можно получить через команду 
`anicli-ru --print-sources`

**Q**: Трейсбеки при получении данных.

**A**: Попробуйте обновить модуль через команду `anicli-ru -U -F` или эквивалентную команду `pip3 install -U anicli-ru`. 
Если это не помогло, то пишите в **issue**

**Q**: Скрипт не запускается из терминала.

**A**: Добавьте в настройки терминала следующую строку:
```bash
# ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"
# ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"
```

---
# Program Api usage
Если вам нужен программный интерфейс для своих проектов, то можете импортировать любой доступный 
парсер из директории anicli_ru.extractors.* или вывести все доступные и импортировать через метод __import\__
```python
# quick example
from anicli_ru.extractors.animania import *
from anicli_ru.loader import all_extractors

print(all_extractors())  # вывод всех доступных парсеров из директории extractors
a = Anime()
ongoings = a.ongoing()  # получить онгоинги
results = a.search("experiments lain")  # поиск тайтла по названию
episodes = results[0].episodes()  # получить эпизоды с первого найденного тайтла
players = episodes[0].player()  # получить сырые ссылки на видеохостниги (не прямую ссылку на видео)
print(players[0].get_video())  # получить прямую ссылку на видео с видеохостинга для плеера
```
---
# Contributing

Скрипт в стадии рефакторинга и улучшения, будет добавлена инструкция позже
