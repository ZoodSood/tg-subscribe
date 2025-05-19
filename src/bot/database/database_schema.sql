-- PromoCodes table for storing promo codes and tracking usage
CREATE TABLE IF NOT EXISTS PromoCodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    max_uses INTEGER,
    used_count INTEGER NOT NULL DEFAULT 0,
    created_by INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT,
    last_redeemed_by INTEGER
);