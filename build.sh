#!/usr/bin/env bash
set -e

echo "============================================="
echo "   Збірка додатку PartsAccounting для Linux   "
echo "============================================="

# Перевірка та активація venv, якщо існує
if [ -d ".venv" ]; then
    echo "Використовується віртуальне оточення .venv"
    source .venv/bin/activate
fi

# Очищення старих артефактів
echo "Очищення build/ та dist/..."
rm -rf build dist

# Запуск PyInstaller
echo "Запуск PyInstaller..."
pyinstaller \
    --name "PartsAccounting" \
    --windowed \
    --onedir \
    --noconfirm \
    --clean \
    --add-data "db/schema.sql:db" \
    --add-data "resources/fonts:resources/fonts" \
    main.py

echo "============================================="
echo "Збірка успішно завершена!"
echo "Виконуваний файл: dist/PartsAccounting/PartsAccounting"
echo "============================================="
