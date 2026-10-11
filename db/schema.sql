-- Схема бази даних (3НФ) для обліку автозапчастин
PRAGMA foreign_keys = ON;

-- Користувачі системи
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'storekeeper')),
    full_name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Категорії запчастин
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

-- Марки автомобілів
CREATE TABLE IF NOT EXISTS car_brands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- Моделі автомобілів
CREATE TABLE IF NOT EXISTS car_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id INTEGER NOT NULL REFERENCES car_brands(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    year_from INTEGER,
    year_to INTEGER,
    UNIQUE(brand_id, name)
);

-- Запчастини
CREATE TABLE IF NOT EXISTS parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_number TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    price REAL NOT NULL CHECK(price >= 0),
    stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK(stock_quantity >= 0),
    min_stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK(min_stock_quantity >= 0),
    unit TEXT NOT NULL DEFAULT 'шт.'
);

-- Сумісність запчастин з моделями авто (багато до багатьох)
CREATE TABLE IF NOT EXISTS part_compatibility (
    part_id INTEGER NOT NULL REFERENCES parts(id) ON DELETE CASCADE,
    model_id INTEGER NOT NULL REFERENCES car_models(id) ON DELETE CASCADE,
    PRIMARY KEY (part_id, model_id)
);

-- Постачальники
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    phone TEXT,
    email TEXT,
    address TEXT
);

-- Покупці (клієнти)
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    address TEXT
);

-- Документи (прибуткові та видаткові накладні)
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_type TEXT NOT NULL CHECK(doc_type IN ('incoming', 'outgoing')),
    doc_number TEXT NOT NULL UNIQUE,
    doc_date TEXT NOT NULL,
    counterparty_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Позиції документів
CREATE TABLE IF NOT EXISTS document_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    part_id INTEGER NOT NULL REFERENCES parts(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    price REAL NOT NULL CHECK(price >= 0)
);

-- Індекси для оптимізації пошуку та зовнішніх ключів
CREATE INDEX IF NOT EXISTS idx_car_models_brand ON car_models(brand_id);
CREATE INDEX IF NOT EXISTS idx_parts_category ON parts(category_id);
CREATE INDEX IF NOT EXISTS idx_parts_part_number ON parts(part_number);
CREATE INDEX IF NOT EXISTS idx_parts_name ON parts(name);
CREATE INDEX IF NOT EXISTS idx_part_compat_model ON part_compatibility(model_id);
CREATE INDEX IF NOT EXISTS idx_documents_type_date ON documents(doc_type, doc_date);
CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_doc_items_doc ON document_items(document_id);
CREATE INDEX IF NOT EXISTS idx_doc_items_part ON document_items(part_id);
