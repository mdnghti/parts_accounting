import hashlib
import os
import sqlite3


def hash_password(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    """Хешування пароля за допомогою PBKDF2-HMAC-SHA256 з сіллю."""
    if salt_hex is None:
        salt = os.urandom(16)
        salt_hex = salt.hex()
    else:
        salt = bytes.fromhex(salt_hex)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return key.hex(), salt_hex


def seed_initial_data(conn: sqlite3.Connection) -> None:
    """Заповнення бази початковими тестовими даними."""
    cur = conn.cursor()

    # 1. Користувачі
    admin_hash, admin_salt = hash_password("admin123")
    keeper_hash, keeper_salt = hash_password("keeper123")

    cur.execute(
        """
        INSERT OR IGNORE INTO users (username, password_hash, salt, role, full_name)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("admin", admin_hash, admin_salt, "admin", "Адміністратор Системи"),
    )
    cur.execute(
        """
        INSERT OR IGNORE INTO users (username, password_hash, salt, role, full_name)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("keeper", keeper_hash, keeper_salt, "storekeeper", "Комірник Іваненко"),
    )

    # 2. Категорії
    categories = [
        ("Фільтри", "Масляні, повітряні, паливні та салонні фільтри"),
        ("Гальмівна система", "Колодки, диски, супорти, гальмівні шланги"),
        ("Підвіска та рульове", "Амортизатори, важелі, сайлентблоки, кермові тяги"),
        ("Двигун та запалювання", "Свічки запалювання, ремені ГРМ, помпи, прокладки"),
        ("Трансмісія", "Комплекти зчеплення, вали, маховики"),
        ("Електрика та освітлення", "Стартери, генератори, лампи, датчики"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)",
        categories,
    )

    # 3. Марки авто
    brands = [
        ("Toyota",),
        ("Volkswagen",),
        ("Renault",),
        ("BMW",),
        ("Ford",),
    ]
    cur.executemany("INSERT OR IGNORE INTO car_brands (name) VALUES (?)", brands)

    # 4. Моделі авто
    # Отримуємо ID брендів
    cur.execute("SELECT id, name FROM car_brands")
    brand_map = {row["name"]: row["id"] for row in cur.fetchall()}

    models = [
        (brand_map["Toyota"], "Corolla", 2012, 2018),
        (brand_map["Toyota"], "Camry", 2015, 2022),
        (brand_map["Toyota"], "RAV4", 2013, 2019),
        (brand_map["Volkswagen"], "Golf VII", 2012, 2020),
        (brand_map["Volkswagen"], "Passat B7", 2010, 2015),
        (brand_map["Volkswagen"], "Tiguan", 2016, 2023),
        (brand_map["Renault"], "Megane III", 2008, 2016),
        (brand_map["Renault"], "Duster", 2010, 2018),
        (brand_map["Renault"], "Logan II", 2012, 2020),
        (brand_map["BMW"], "3 Series (F30)", 2011, 2019),
        (brand_map["BMW"], "5 Series (F10)", 2010, 2017),
        (brand_map["BMW"], "X5 (F15)", 2013, 2018),
        (brand_map["Ford"], "Focus III", 2011, 2018),
        (brand_map["Ford"], "Mondeo V", 2014, 2022),
        (brand_map["Ford"], "Kuga II", 2012, 2019),
    ]
    cur.executemany(
        """
        INSERT OR IGNORE INTO car_models (brand_id, name, year_from, year_to)
        VALUES (?, ?, ?, ?)
        """,
        models,
    )

    # 5. Постачальники
    suppliers = [
        ("ТОВ 'АвтоТрейд Постач'", "+380501112233", "supply@autotrade.ua", "м. Київ, вул. Перемоги, 10"),
        ("ПП 'Глобал Партс'", "+380672223344", "info@globalparts.ua", "м. Львів, вул. Городоцька, 50"),
        ("ТОВ 'Омега Автопостачання'", "+380633334455", "contact@omega-auto.ua", "м. Харків, вул. Шевченка, 120"),
    ]
    cur.executemany(
        """
        INSERT OR IGNORE INTO suppliers (name, phone, email, address)
        VALUES (?, ?, ?, ?)
        """,
        suppliers,
    )

    # 6. Клієнти
    customers = [
        ("ФОП Мельник В.О.", "+380991110022", "melnyk.auto@gmail.com", "м. Київ, вул. Кільцева, 4"),
        ("СТО 'АвтоМайстер'", "+380982220033", "automaster@ukr.net", "м. Київ, вул. Польова, 15"),
        ("Ткаченко Сергій Іванович", "+380933330044", "tkachenko.s@gmail.com", "м. Бориспіль, вул. Київська, 22"),
        ("СТО 'Драйв Плюс'", "+380674440055", "driveplus@meta.ua", "м. Бровари, вул. Незалежності, 8"),
    ]
    cur.executemany(
        """
        INSERT OR IGNORE INTO customers (name, phone, email, address)
        VALUES (?, ?, ?, ?)
        """,
        customers,
    )

    # 7. Запчастини
    cur.execute("SELECT id, name FROM categories")
    cat_map = {row["name"]: row["id"] for row in cur.fetchall()}

    parts = [
        ("OF-1001", "Фільтр масляний Mann W67/2", cat_map["Фільтри"], 280.00, 24, 5, "шт."),
        ("OF-1002", "Фільтр масляний Bosch P4020", cat_map["Фільтри"], 320.00, 18, 5, "шт."),
        ("AF-2001", "Фільтр повітряний Knecht LX1211", cat_map["Фільтри"], 450.00, 12, 4, "шт."),
        ("AF-2002", "Фільтр повітряний Filtron AP185", cat_map["Фільтри"], 310.00, 4, 5, "шт."),
        ("CF-3001", "Фільтр салону вугільний Mahle LAK855", cat_map["Фільтри"], 520.00, 8, 3, "шт."),
        ("FF-4001", "Фільтр паливний Purflux CS762", cat_map["Фільтри"], 680.00, 3, 5, "шт."),
        ("BP-5001", "Колодки гальмівні передні Ferodo FDB1788", cat_map["Гальмівна система"], 1250.00, 15, 4, "компл."),
        ("BP-5002", "Колодки гальмівні передні Brembo P85075", cat_map["Гальмівна система"], 1480.00, 10, 3, "компл."),
        ("BP-5003", "Колодки гальмівні задні TRW GDB1330", cat_map["Гальмівна система"], 980.00, 2, 4, "компл."),
        ("BD-6001", "Диск гальмівний вентильований Brembo 09.9145.11", cat_map["Гальмівна система"], 2100.00, 6, 2, "шт."),
        ("SA-7001", "Амортизатор передній Kayaba Excel-G 334812", cat_map["Підвіска та рульове"], 2400.00, 8, 2, "шт."),
        ("SA-7002", "Амортизатор задній Sachs 313052", cat_map["Підвіска та рульове"], 1950.00, 7, 2, "шт."),
        ("CA-8001", "Важіль передньої підвіски Lemforder 35324", cat_map["Підвіска та рульове"], 3150.00, 5, 2, "шт."),
        ("SP-9001", "Свічка запалювання NGK BKR6E-11", cat_map["Двигун та запалювання"], 190.00, 40, 10, "шт."),
        ("SP-9002", "Свічка запалювання Denso Iridium IK20", cat_map["Двигун та запалювання"], 420.00, 16, 8, "шт."),
        ("TB-1001", "Ремінь ГРМ Gates 5499XS", cat_map["Двигун та запалювання"], 850.00, 9, 3, "шт."),
        ("WP-1101", "Насос охолоджуючої рідини SKF VKPC81418", cat_map["Двигун та запалювання"], 1750.00, 4, 2, "шт."),
        ("CK-1201", "Комплект зчеплення LuK 624318009", cat_map["Трансмісія"], 6200.00, 3, 1, "компл."),
        ("ST-1301", "Стартер 12V 1.4kW Valeo 438179", cat_map["Електрика та освітлення"], 4800.00, 2, 1, "шт."),
        ("GN-1401", "Генератор 140A Bosch 0124525091", cat_map["Електрика та освітлення"], 7500.00, 1, 1, "шт."),
    ]
    cur.executemany(
        """
        INSERT OR IGNORE INTO parts
        (part_number, name, category_id, price, stock_quantity, min_stock_quantity, unit)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        parts,
    )

    # 8. Сумісність запчастин з моделями авто
    cur.execute("SELECT id, part_number FROM parts")
    part_map = {row["part_number"]: row["id"] for row in cur.fetchall()}

    cur.execute("SELECT id, name FROM car_models")
    model_name_map = {row["name"]: row["id"] for row in cur.fetchall()}

    compatibilities = [
        (part_map["OF-1001"], model_name_map["Corolla"]),
        (part_map["OF-1001"], model_name_map["Camry"]),
        (part_map["OF-1001"], model_name_map["RAV4"]),
        (part_map["OF-1002"], model_name_map["Golf VII"]),
        (part_map["OF-1002"], model_name_map["Passat B7"]),
        (part_map["OF-1002"], model_name_map["Tiguan"]),
        (part_map["AF-2001"], model_name_map["Corolla"]),
        (part_map["AF-2001"], model_name_map["RAV4"]),
        (part_map["AF-2002"], model_name_map["Megane III"]),
        (part_map["AF-2002"], model_name_map["Logan II"]),
        (part_map["CF-3001"], model_name_map["3 Series (F30)"]),
        (part_map["CF-3001"], model_name_map["5 Series (F10)"]),
        (part_map["FF-4001"], model_name_map["Duster"]),
        (part_map["FF-4001"], model_name_map["Logan II"]),
        (part_map["BP-5001"], model_name_map["Focus III"]),
        (part_map["BP-5001"], model_name_map["Mondeo V"]),
        (part_map["BP-5002"], model_name_map["Golf VII"]),
        (part_map["BP-5002"], model_name_map["Passat B7"]),
        (part_map["BP-5003"], model_name_map["Golf VII"]),
        (part_map["BP-5003"], model_name_map["Passat B7"]),
        (part_map["BD-6001"], model_name_map["Golf VII"]),
        (part_map["BD-6001"], model_name_map["Passat B7"]),
        (part_map["SA-7001"], model_name_map["Corolla"]),
        (part_map["SA-7001"], model_name_map["RAV4"]),
        (part_map["SA-7002"], model_name_map["3 Series (F30)"]),
        (part_map["CA-8001"], model_name_map["Focus III"]),
        (part_map["CA-8001"], model_name_map["Kuga II"]),
        (part_map["SP-9001"], model_name_map["Megane III"]),
        (part_map["SP-9001"], model_name_map["Logan II"]),
        (part_map["SP-9001"], model_name_map["Duster"]),
        (part_map["SP-9002"], model_name_map["Corolla"]),
        (part_map["SP-9002"], model_name_map["Camry"]),
        (part_map["TB-1001"], model_name_map["Focus III"]),
        (part_map["TB-1001"], model_name_map["Mondeo V"]),
        (part_map["WP-1101"], model_name_map["Golf VII"]),
        (part_map["WP-1101"], model_name_map["Passat B7"]),
        (part_map["CK-1201"], model_name_map["Focus III"]),
        (part_map["ST-1301"], model_name_map["Megane III"]),
        (part_map["ST-1301"], model_name_map["Duster"]),
        (part_map["GN-1401"], model_name_map["Passat B7"]),
        (part_map["GN-1401"], model_name_map["Tiguan"]),
    ]
    cur.executemany(
        """
        INSERT OR IGNORE INTO part_compatibility (part_id, model_id)
        VALUES (?, ?)
        """,
        compatibilities,
    )

    conn.commit()
