#!/bin/sh
exec python3 "$(dirname "$(realpath "$0")")/anicli_ru/__main__.py" "$@"