# anicli-ru

---

CLI приложение и локальный вебсервер для поиска и просмотра аниме из терминала с русской озвучкой или субтитрами.
Поддерживает unix, linux, windows 10/11 (через windows terminal)

## Demonstration
TODO pass video CLI DEMO 

TODO pass video  WEB DEMOG


## Index

* [Установка](#Установка)
    * [API interface](#API-interface)
* [Usage](#Usage)
    * [Check Updates](#Check-Updates)
* [CLI](#CLI)
    *[interface](#interface)
* [WEB](#WEB)
* [Command Reference](#Command-Reference)
    * [Commands](#Commands)
        * [version](#version)
        * [update](#update)
        * [check-updates](#check-updates)
        * [web](#web)
        * [cli](#cli)
    * [Notes](#Notes)
* [License](#License)
## Установка

- Требуется python 3.9 или выше
- Для CLI требуется [mpv видеоплеер](https://github.com/mpv-player/mpv)
- Проект поставляется через pip, рекомендуется устанавливать через [uv](https://docs.astral.sh/uv/guides/tools/#installing-tools) или [pipx](pipx.pypa.io/latest/getting-started/)
- Минимальная установка, только CLI клиент
    - UV - `uv tool install anicli-ru` (рекомендуется)
    - PIPX - `pipx install anicli-ru`

### Опциональные зависимости:

- Установка всех зависимостей (CLI + webserver + browser cookie extractor)
    - `uv tool install anicli-ru[all]`
    - `pipx install anicli-ru[all]`

- Извлечение cookies из браузера в клиент (используется для редкого обхода ddos-guard/cloudflare, требуется зависимость [rookiepy](https://github.com/thewh1teagle/rookie))
    - `uv tool install anicli-ru[cookies]`
    - `pipx install anicli-ru[cookies]`
- Локальный веб клиент
    - `uv tool install anicli-ru[web]`
    - `pipx install anicli-ru[cookies]`

- termux webclient (TODO, untested)

> TODO: add install script for termux (кто протестирует - можете закинуть PR с shell скриптом установки)

Предполагаю, что локальный клиент должен работать в android termux эмуляторе. 
Для работоспособности требуются следующие зависимости:

```shell
pkg install python-dev libxml2-dev libxslt-dev libiconv-dev
```

Затем скачать проект, установить пакеты и запустить

### API interface

Клиент и парсеры умышленно разделены в отдельные репозитории: чтобы мне было удобнее экспериментировать и исправлять и сторонним пользователям использовать в проекте.

Если только нужны готовые парсеры и API интрефейс, используйте библиотеку https://github.com/vypivshiy/anicli-api

## Usage

Для вывода информации о коммандах используйте:

```shell
anicli-ru --help
```

доступных опции:

```shell
anicli-ru cli --help 
```

Вывод установленной версии клиента и API

```shell
anicli-ru version
```

### Check Updates

> работает если установлен через uv или pipx, иначе необходимо вручную обновлять

Проверить обновления

```shell
anicli-ru check-updates
```

Установить обновления:

```shell
anicli-ru update
```

принудительно переустановить:

```shell
anicli-ru update --force 
```

### CLI

Реализован поверх [prompt-toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit), визуализация вывода идёт через [rich](https://github.com/Textualize/rich), воспроизведение видео через [mpv](https://github.com/mpv-player/mpv) плеер.

Вывод всех доступных источников:

> Дополнительная информация об источниках описана в [anicli-api/source-description](https://github.com/vypivshiy/anicli-api?tab=readme-ov-file#source-description)


```shell
anicli-ru cli
```

Запуск поиска при старте. 

```shell
anicli-ru cli -s animego --search isekai
```

Запуск ongoing при старте

```shell
anicli-ru cli -s animego --ongoing
```

Понижение качества доступных видео (выбирает самый ближайший)

```shell
# например, для kodik это 360, для dreamcast - 1080
anicli-ru cli -s animego -q 360
```

#### interface

- Нажимайте `<tab>` кнопку или начинайте вводить - выведутся доступные команды
- search, ongoing - есть простой фильтр по названию тайтла - вводите символы в назваии тайтла - они поднимутся вверх в автодополнении

Episodes:

Для эпизодов есть фильтр по номерам. Индекс начинается с 1.

Примеры:

1. выбрать 1, 3 и 5 эпизод:

```
1 3 5
```

2. выбрать 1, 3 и с 5 по 10:

```
1 3 5-10
```

3. если ошибетесь и добавите лишние данные - фильтр откорректируется автоматически:

например при вводе
```
1 1 2 3 1-2
```

финальный фильтр:

```
1-3
```

4. Воспроизведение серии видео

- создаёт временный файл-плейлист. 
    - в unix/linux записывает в директорию `/tmp`, 
    - в windows - в директорию `%TMP%` (по умолчанию `C:\Users\<USERNAME>\AppData\Local\Temp`)
- размер плейлиста зависит от ключа `--m3u-size` (по умолчанию, значение 6).
- не рекомендуется увеличивать значение если не планируете всё смотеть "в один присест", так как ссылки на видео живут примерно 24 часа
- автоматически собирает плейлист на основе значений источника и даббера. 
    - Например, если вы выбрали Ongoing и озвучку "Субтитры", а для последнего он отсутвует (но есть Animevost) - поток прервётся.

### WEB

>[!warning]
> Реализован для локального использования, категорически не рекомендуется применять в production и(или) публичной сети. 
> Не рассчитан для выполнения 24/7
>
> Да я ваибкодил его, но также затерпел и **вайбдебажил и вайбтестил его** 

Простой вебклиент со статическим рендером страниц и встроенным reverse-proxy трансляции видео в плеер.

Стек сервера:
- backend: [fastapi](https://github.com/fastapi/fastapi)
- frontend: pure js, [water.css](https://watercss.kognise.dev/)
- видеоплеер - [Artplayer.js](https://artplayer.org/) и плагины hls.js, dash.js
- не применяются базы данных - данные кешируются в ОЗУ процесса сервера

Для запуска требуется установить зависимость:
    - uv tool install `ani-cli-ru[web]`
    - pipx install `ani-cli-ru[web]`

запускать командой:

```shell
anicli-ru web
```

Для прочих настроек (ip, port, ttl) введите

```shell
anicli-ru web --help
```

Входить по ссылке со сгенерированным токеном или сканировать QR код.
Пример вывода ссылки для входа:

```
Server started at: http://127.0.0.1:8000/?token=HSB6l1qzoBogpPNpBakXhA
```

В search/ongoing/episode страницах доступны фильтры по заголовку и номерам эпизодов. 
Синтаксис поиска номера эпизода идентичен как в CLI

## Command Reference

### Commands

#### version

**Description:** Напечатать версию приложения и anicli-api

**Usage:**
```
anicli version
```

#### update

**Description:** Обновить приложение 

>[!note]
> Работает если установлено в pipx или uv, в обычном pip нужно обновлять вручную

**Usage:**
```
anicli update [--force]
```

**Options:**
- `--force`: Принудительно обновить api и клиент

#### check-updates

**Description:** Проверить наличие обновлений на pypi

**Usage:**
```
anicli check-updates
```

#### web

**Description:** Запустить локальный сервер (experimental, LOCAL USE ONLY)

**Usage:**
```
anicli web [OPTIONS]
```

**Options:**
- `-h, --host TEXT`: IP host (default: 127.0.0.1)
- `-p, --port INTEGER`: Port (default: 8000)
- `-mw, --max-workers INTEGER`: Uvicorn max workers (default: 1)
- `-c, --chunk-size TEXT`: Размер чанка видеопотока для трансляции в вебплеер. Поддерживает суффиксы: k/K (kbytes), m/M (mbytes), или число (bytes) (по умолчанию: 1M - 1 мегабайт)
- `-s, --source TEXT`: Источник (можно переключить в веб интерфейсе)
- `--ttl TEXT`: Cache TTL - через сколько уничтожишь извлеченные объекты. Поддерживает суффиксы: h/H (hours), m/M (minutes), или число (seconds) (default: 12h)

#### cli

**Description:** Запуск интерактивного cli приложения (требуется mpv видеоплеер)
**Usage:**
```
anicli cli [OPTIONS]
```

**Required Options:**
- `-s, --source TEXT`: Источник (можно изменить в приложении)

**Optional Options:**
- `-q, --quality INTEGER`: Качество видео по умолчанию. Если оно недоступно - выберет близжайшее значение. (default: 2060)
- `--search TEXT`: При запуске вывести результат поиска тайтлов по запросу 
- `--ongoing`: При запуске вывести доступные онгоинги
- `-mo, --mpv-opts TEXT`: Дополнительные MPV опции. Должны быть одной строкой. Пример: `"-config=/.config/mpv/mpv.conf --no-audio"`
- `--m3u-size INTEGER`: Максимальный размер плейлиста (slice-play) (default: 6). Не рекомендуется увеличивать размер - извлечённые ссылки имеют срок жизни и не живут долго!
- `--timeout INTEGER`: HTTP client timeout (seconds) (default: 60)
- `--proxy TEXT`: Прокси для клиента. поддерживает http(s), socks4/5. Имеет формат scheme://user:password@host:port
- `--cookies-from-browser TEXT`: Извлечь cookies из браузера и загрузить в httpx клиент. Требуется зависимость `anicli[cookies]`
- `--cookies PATH`: прочитать cookie из файла (должны быть в netscape формате)
- `-H, --header TEXT`: Добавить http заголовки в клиент, можно передать несколько раз (формат: Key=Value)
- `--header-file PATH`: Путь до файла с заголовками headers (формат на одну строку:, Key=Value)

### Notes

- The `web` command is experimental and intended for local network use only, not suitable for production deployment
- The `cli` command requires an MPV player to be installed and available in your system PATH
- Both `--search` and `--ongoing` options cannot be used simultaneously in the cli command
- Chunk size and TTL options support various suffixes for convenience:
  - Chunk size: k/K for kilobytes, m/M for megabytes, or plain integer for bytes
  - TTL: h/H for hours, m/M for minutes, or plain integer for seconds


## License

GPL3