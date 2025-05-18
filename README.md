# anicli-ru

---

Скрипт для поиска и просмотра аниме из терминала с русской озвучкой или субтитрами.
Поддерживает unix, linux, windows 10/11 (windows terminal)

https://github.com/vypivshiy/ani-cli-ru/assets/59173419/bf7e78bd-cdd1-4871-a5b3-f48e6ed7ec28

## Установка

- Поддерживает python 3.8 или выше
- требуется [mpv видеоплеер](https://github.com/mpv-player/mpv)

| менеджер пакетов                                                       | установка                   | обновление                        |
|------------------------------------------------------------------------|-----------------------------|-----------------------------------|
| [uv (рекомендуется)](https://docs.astral.sh/uv/#installation)          | `uv tool install anicli-ru` | `uv tool upgrade anicli-ru`       |
| [pipx](https://pipx.pypa.io/stable/installation/)                      | `pipx install anicli-ru`    | `pipx upgrade anicli-ru`          |
| [pip (не рекомендуется см PEP 668)](https://peps.python.org/pep-0668/) | `pip install anicli-ru`     | `pip install anicli-ru --upgrade` |

Если нужен только программный python api интерфейс парсеров для проекта используйте библиотеку [anicli-api](https://github.com/vypivshiy/anicli-api)

Опциональная зависимость для извлечения cookies из браузера

>[!note]
> 
> Эта опция ситуативная и может пригодиться только в крайних случаях для обхода cloudflare или ddos guard.
> Работает как опция в yt-dlp `--cookies-from-browser`.
> Вы можете вручную экспортировать cookies из браузера в netscape формат и передать аргументом (ниже будет пример) без установки дополнительной зависимости

Установка с зависимостью экспорта cookies с браузера:

| менеджер пакетов                                  | установка                                    | обновление                        |
|---------------------------------------------------|----------------------------------------------|-----------------------------------|
| [uv](https://docs.astral.sh/uv/#installation)     | `uv tool install anicli-ru[browser-cookies]` | `uv tool upgrade anicli-ru`       |
| [pipx](https://pipx.pypa.io/stable/installation/) | `pipx install anicli-ru[browser-cookies] `   | `pipx upgrade anicli-ru`          |
| [pip](https://peps.python.org/pep-0668/)          | `pip install anicli-ru[browser-cookies] `    | `pip install anicli-ru --upgrade` |


Добавление зависимости экпорта cookies с браузера:

| менеджер пакетов                                                       | установка                                                     |
|------------------------------------------------------------------------|---------------------------------------------------------------|
| [uv](https://docs.astral.sh/uv/#installation)                          | `uv tool install anicli-ru --with anicli-ru[browser-cookies]` |
| [pipx](https://pipx.pypa.io/stable/installation/)                      | `pipx inject anicli-ru anicli-ru[browser-cookies] `           | 
| [pip (не рекомендуется см PEP 668)](https://peps.python.org/pep-0668/) | `pip install anicli-ru[browser-cookies] `                     |


## Nix

- Во [флейке](./flake.nix) имеются:

  1. packages `nix run github:vypivshiy/ani-cli-ru`, a также вместо `run` `build` для `./result`
  2. devShells `nix shell github:vypivshiy/ani-cli-ru`
  3. overlays `pkgs.anicli-ru -> inputs.anicli-ru.packages.<system>.default` ! может не работать

- Установка:

  1. system-wide `environment.systemPackages = [ pkgs.anicli-ru ];`
  2. user-only `home.packages = [ pkgs.anicli-ru ];`

## Usage:

```shell
anicli-ru
```

### Примеры:

#### Сменить источник:

```shell
anicli-ru -s anilibria
```

#### Запуск поиска/онгоингов при старте:

```shell
# запуск и поиск тайтлов по фразе `lain`
anicli-ru --search "lain"
# запуск и вывод онгоингов
anicli-ru --ongoing
```

#### Передача дополнительных аргументов в плеер.

Например, если у вас специально настроенный профиль в mpv плеере:

```shell
anicli-ru -pa="--profile=my_profile"
```

#### Установка cookies в http запросы

>[!tip]
> передача cookies **может** пригодится для обхода cloudflare или ddos-guard, редко пригождается

Эта опция читает [netscape формат](https://curl.se/rfc/cookie_spec.html). 
Cookie из браузера можно, например, импортировать через firefox плагин [cookies-txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
и прочим аналогам.

> cookies.txt
```
.example.com	TRUE	/	FALSE	1747566077	cookie	test123
.example.com	TRUE	/	FALSE	1747566077	cookie2	foobar
```

```shell
anicli-ru --cookies netscape-cookies.txt
```

#### Установка cookies при помощи извлечения из браузера. 

Работает [как в yt-dlp с опцией --cookies-from-browser](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp)

>[!note]
> требуется дополнительная зависимость anicli-ru\[browser-cookies]

```shell
anicli-ru --cookies-from-browser firefox
```

#### Установка headers заголовков

Формат `ключ=значение`.

В источнике `anilibme` после авторизации будет доступен их плеер с разрешением full hd/4k.
После авторизации, можно из браузера извлечь заголовок по ключу `Authorization: Bearer ...`

```shell
anicli-ru -s anilibme --header "Authorization=Bearer ..."
```

Можно передать несколько заголовков

```shell
anicli-ru -s anilibme --header "Authorization=Bearer ..." --header "User-Agent=Mozilla/5.0 ..."
```

Передача заголовков через файл (формат `ключ=значение` на каждую новую строку)

> headers.txt
```
Authorization=Bearer ...
User-Agent=Mozilla/5.0 ...
```

```shell
anicli-ru --header-file headers.txt
```


## Ключи запуска

```
-s --source - выбор источника. По умолчанию "yummy_anime_org"
-q --quality - минимально выбранное разрешение видео. Доступны: 0, 144, 240, 360, 480, 720, 1080, 2060. По умолчанию 2060
  Например, если вы установили 1080 и такое видео отсутстует - выведет максимально допустимое (720 и далее)
--ffmpeg - использовать ffmpeg для перенаправления видеопотока в видеоплеер (DEPRECATED)
-p --player - какой видеоплеер использовать. доступны "vlc", "mpv". По умолчанию "mpv"
  vlc плеер (DEPRECATED)
--m3u - для SLICE-режима просмотра создавать плейлист (ЭКСПЕРИМЕНТАЛЬНЫЙ РЕЖИМ, СОБИРАЕТ ВИДЕО МЕДЛЕННО)
--m3u-size - максимальный размер m3u плейлиста. По умолчанию 12
-pa --playlist-args - дополнительные аргументы для плеера. Например, -pa="--profile=foo" -pa="--no-video".
  подробнее о них смотрите в документации по плееру
--search - запустить и найти тайтл по строке
--ongoing - запустить и найти онгоинги
--cookies - загрузить в клиент cookie (netscape format)
--cookies-from-browser - загрузить в клиент cookies из браузера
--header - дополнительные заголовки для http запросов (формат ключ=значение)
--header-file - дополнительные заголовки для http запросов (формат ключ=значение на каждую строку)
```
