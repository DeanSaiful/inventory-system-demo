CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,
    component_id INTEGER NOT NULL,

    quantity INTEGER NOT NULL CHECK (quantity > 0),

    status TEXT NOT NULL CHECK (
        status IN ('borrowed', 'returned', 'cancelled')
    ) DEFAULT 'borrowed',

    requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    returned_at DATETIME,

    remarks TEXT,

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (component_id) REFERENCES components(id)
);
