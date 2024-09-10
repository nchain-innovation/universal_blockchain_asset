#!/bin/bash

flake8 --ignore=E501,E131,E402,E722 src --exclude src/tx_engine/,src/tools

mypy --check-untyped-defs --ignore-missing-imports src
# mypy src --config-file ./mypy.ini
