CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    violations_qty INTEGER NOT NULL DEFAULT 0 CHECK (violations_qty >= 0)
);

CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    seller_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    name TEXT NOT NULL CHECK (char_length(name) BETWEEN 1 AND 256),
    description TEXT NOT NULL DEFAULT '',
    category INTEGER NOT NULL DEFAULT 0 CHECK (category >= 0),
    images_qty INTEGER NOT NULL DEFAULT 0 CHECK (images_qty >= 0)
);

CREATE INDEX IF NOT EXISTS idx_items_seller_id ON items (seller_id);
