# anicli-ru
[![CI](https://github.com/vypivshiy/ani-cli-ru/actions/workflows/ci.yml/badge.svg)](https://github.com/vypivshiy/ani-cli-ru/actions/workflows/ci.yml)
___
Проект в стадии реставрации и улучшения, 
обновленный скрипт можете установить протестировать в [dev ветке](https://github.com/vypivshiy/ani-cli-ru/tree/dev)

Скрипт для поиска и просмотра аниме из терминала с русской озвучкой или субтитрами для linux систем, 
написанный на python.

Парсит видео со сторонних сайтов, **как youtube-dl**.
___
## Supported video hostings:
* sibnet
* aniboom
* kodik
---
## Dependencies:
* python 3.8+
* requests
* mpv
___

## Install:
### pipx (рекомендуется)
`pipx install anicli-ru`


### pip
```shell
pip install anicli-ru
```

___
## Usage:
`anicli-ru`
___
## CLI Commands:
```
q [q]uit - выход из программы
e [e]xit - alias q
b [b]ack to the previous step - возвратиться на предыдущий шаг
h [h]elp - вывод списка доступных команд
c [c]lear - очистить консоль
o [o]ngoing - напечатать недавно вышедшие онгоинги
```
## FAQ
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
## Program Api usage
### В стадии разработки
Самый актуальный api интерфейс парсеров находится в [anicli-api](https://github.com/vypivshiy/anicli-api/tree/dev) 
репозитории, в этом поддержки кода не будет:

```shell
pip install anicli-api
```

### Устаревший способ
Вы можете использовать напрямую этот пакет
Все реализованые парсеры лежат в модуле `anicli_ru.extractors.*`

```python
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

