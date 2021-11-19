# anicli-ru
___
Скрипт для поиска и просмотра аниме из терминала с русской озвучкой для linux систем, написанный на python.

Парсит аниме с сайта [animego.org](https://animego.org/)

![test](example.svg)
![result](https://i.imgur.com/hGWF07x.png)
___
# Dependencies:
* __mpv__ или видеоплеер, поддерживающий __hls__ и __cli__ команды (проверялся скрипт на mpv,
стабильность с другими плеерами не гарантирована)
* python 3.6+
* requests
___
# Install:
**CLI tool:**
```
git clone https://github.com/vypivshiy/ani-cli-ru.git
cd ani-cli-ru
sudo make
```
**Если нужен только доступ к API интерфейсу без установки CLI скрипта:**
```
git clone https://github.com/vypivshiy/ani-cli-ru.git
cd ani-cli-ru
python3 setup.py install
```
**Или:**
```
pip install anicli_ru
```
___
# Usage:
`anicli-ru`
___
# Supported video hostings:
* sibnet
* aniboom
* kodik
* anivod (kodik mirror)
___
# CLI Commands:
```
q [q]uit - выход из программы
b [b]ack to the previous step - возвратиться на предыдущий шаг
h [h]elp - вывод списка доступных команд
c [c]lear - очистить консоль
o [o]ngoing print - напечатать недавно вышедшие онгоинги
r [r]andom title - выбрать случайное аниме и напечатать доступные эпизоды (через эндпоинт сайта)
```
# Optional arguments:
**-p --proxy** - опциональный аргумент на установку прокси. Если просмотр аниме (или некоторых тайтлов) 
запрещен в вашей стране, то это поможет обойти ограничения (Только на получение ссылки на видео, 
сама загрузка видео будет идти без прокси, так как там ограничений нет)

Пример ввода прокси:
    
    anicli-ru --proxy https://192.168.0.1:8080  # HTTPS
    
    anicli-ru --proxy socks4://192.168.0.1:8888  # SOCKS4
    
    anicli-ru --proxy socks5://192.168.0.1:8888  # SOCKS5

**-v --videoplayer** - опциональный аргумент выбора локального видеоплеера. По умолчанию mpv.

**-hc --headers-command** - опциональный аргумент команды установки заголовка headers в выбранном плеере.
По умолчанию --http-header-fields (как в mpv)
___
# Api usage example:
```python
from anicli_ru import Anime
from anicli_ru.utils import run_player


anime = Anime()
ongoings = anime.ongoing() # get ongoings
# get first ongoing title, first episode and first videoplayer
url_ong = ongoings[0].episodes()[0].player()[0].get_video()

rezults = anime.search("lain")
rezults.print_enumerate()
# get first find result:
a = rezults.choose(1)  # index start in 1 or usage list index: rezults[0]
episodes = a.episodes()
ep = episodes.choose(1)  # choose episode 1
players = ep.player()  # get players. lain return 1 with X-Media dub
p = players.choose(1)
url = p.get_video()  # get direct video url
# if need send video to local player, import run_player (player arg default mpv)
run_player(url)
```
---
# ROADMAP:

- [x] добавить поддержку proxy;
- [x] вывод вышедших на сегодняшнюю дату онгоингов;
- [ ] рефакторинг логики работы меню;
- [ ] выбор качества видео;
- [ ] добавление фич;
- [ ] добавить дополнительные команды управления через argparser;