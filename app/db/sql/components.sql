CREATE TABLE IF NOT EXISTS components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    value TEXT,
    size TEXT,
    voltage TEXT,
    watt TEXT,
    type TEXT,
    part_no TEXT UNIQUE,
    rack TEXT,
    location TEXT,
    quantity INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
