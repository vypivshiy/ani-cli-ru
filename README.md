# anicli-ru

___
Скрипт для поиска и просмотра аниме из терминала с русской озвучкой или субтитрами для linux систем, 
написанный на python.

> !!! Этот проект в стадии разработки, возможны (будут точно) баги и ошибки

https://github.com/vypivshiy/ani-cli-ru/assets/59173419/bf7e78bd-cdd1-4871-a5b3-f48e6ed7ec28

## Установка

**Рекомендуется использовать pipx**

```shell
pipx install -U git+https://github.com/vypivshiy/ani-cli-ru.git@dev 
```

## Usage:
```shell
anicli-ru

```

> у вас должен быть установлен `mpv` плеер

---
Отличия от старой версии (кроме как переписан):

- [Api интерфейс парсера](https://github.com/vypivshiy/anicli-api/tree/dev) и Cli клиента 
разделены в отдельные репозитории. Также, API интерфейс поддерживает asyncio!
- http клиент заменен с `requests` на `httpx` с включенным по умолчанию **http2** протоколом.
- парсеры работают в связке `httpx`, `parsel`, `chompjs` вместо одних регулярными выражений (как в yt-dlp)
- Использует экспериментальную обёртку [scrape-schema](https://github.com/vypivshiy/scrape-schema) для 
повышения ремонтопригодности, консистентности, читабельности и переиспользуемости кода 
~~если вы знаете что такое css, xpath серекторы и parsel~~.
- Клиент основан на prompt-toolkit, реализована надстройка [eggella](https://github.com/vypivshiy/eggella) - 
архитектура схожа с flask и фреймворками чат ботов (aiogram, discord.py, ...))


## Roadmap
- [x] минимальная реализация
- [x] выбор источника
- [ ] http сервер-прослойка для передачи видео в плееры отличные от mpv (для обхода отсутствия 
аргументов настройки заголовков как в vlc, например)
- [ ] конфигурация http клиента (прокси, таймаут)
- [ ] кеширование
- [ ] синхронизация с shikimori
- [ ] поиск и переключение по нескольким источникам в одной сессии (без перезапуска)
- [ ] конфигурация приложения
- [ ] система плагинов, кастомизация (?)



