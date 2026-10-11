# Автоматизована система обліку запчастин легкових автомобілів

Курсовий проект: десктопний додаток для складського обліку автозапчастин.

## Стек технологій

- **Мова програмування**: Python 3.11+
- **Графічний інтерфейс**: PySide6 (Qt)
- **База даних**: SQLite 3 (`sqlite3`, без ORM, чистий SQL з параметризацією)
- **Звіти**: openpyxl (Excel), reportlab (PDF)
- **Тестування**: pytest
- **Збірка**: PyInstaller (Windows `.exe` та Linux бінарник)

## Структура проекту

```text
parts_accounting/
├── main.py                     # Точка входу додатку
├── requirements.txt            # Залежності проекту
├── build.sh                    # Локальна збірка під Linux
├── LICENSE                     # Ліцензія MIT
├── README.md                   # Документація проекту
├── .gitignore
├── db/                         # Схема БД, підключення, початкові дані
│   ├── connection.py
│   ├── schema.sql
│   └── seed_data.py
├── models/                     # Dataclass-моделі сутностей
├── services/                   # Бізнес-логіка (прихід, розхід, залишки, аутентифікація)
├── ui/                         # Вікна та форми PySide6
├── reports/                    # Генерація звітів (Excel, PDF)
└── tests/                      # Модульні та інтеграційні тести (pytest)
```

## Встановлення та запуск

### 1. Клонування репозиторію

```bash
git clone https://github.com/mdnghti/parts_accounting.git
cd parts_accounting
```

### 2. Створення віртуального оточення та встановлення залежностей

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux / macOS
# .venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

### 3. Запуск додатку

```bash
python main.py
```

При першому запуску автоматично створюється файл бази даних `parts_accounting.db` та заповнюється тестовими даними.

### Облікові записи за замовчуванням

- **Адміністратор**: логін `admin`, пароль `admin123`
- **Комірник**: логін `keeper`, пароль `keeper123`

## Ліцензія

Проект розповсюджується за ліцензією [MIT](LICENSE).
