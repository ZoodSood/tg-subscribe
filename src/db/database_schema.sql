CREATE TABLE IF NOT EXISTS "Users" (
	"id"	INTEGER,
	"telegram_id"	INTEGER,
	"first_name"	TEXT,
	"last_name"	TEXT,
	"username"	TEXT,
	"days_sub_end"	TEXT,
	"balance" INTEGER,
	"invite_link" TEXT,
	"is_banned" INTEGER DEFAULT 0,
	"last_active" TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE IF NOT EXISTS "Transactions" (
	"id"	INTEGER,
	"txid"	TEXT,
	"owner_telegram_id" INTEGER,
	"status" BOOLEAN,
	"weeks" INTEGER,
	"created_at_timestamp" INTEGER,
	PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE IF NOT EXISTS "PromoCodes" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "code" TEXT UNIQUE NOT NULL,
    "is_active" INTEGER DEFAULT 1,
    "max_uses" INTEGER DEFAULT 0,
    "used_count" INTEGER DEFAULT 0,
    "created_by" INTEGER,
    "created_at" TEXT,
    "expires_at" TEXT,
    "last_redeemed_by" INTEGER
);
