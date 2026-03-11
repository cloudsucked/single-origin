from __future__ import annotations

import sqlite3
from pathlib import Path

from app.config import settings


def db_path() -> Path:
    return Path(settings.database_path)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                origin TEXT,
                roast_level TEXT,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                price REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                total REAL NOT NULL,
                status TEXT NOT NULL,
                billing_address TEXT NOT NULL,
                card_last4 TEXT NOT NULL,
                phone TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                plan TEXT NOT NULL,
                frequency TEXT NOT NULL,
                status TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def seed_db() -> None:
    users = [
        ("demo@singleorigin.example", "CoffeeIsLife2026!", "Alex Demo", "customer"),
        ("wholesale@cafepartner.example", "Partner2026!", "Cafe Partner Co.", "wholesale_partner"),
        ("admin@singleorigin.example", "Admin2026!", "Admin User", "admin"),
    ]
    users.extend(
        [(f"test{i}@example.com", "Test2026!", f"Test User {i}", "customer") for i in range(1, 51)]
    )

    products = [
        (1, "Yirgacheffe Reserve", "yirgacheffe-reserve", "Ethiopia", "light", "beans", "Blueberry and jasmine notes", 22.0),
        (2, "Huila Valley", "huila-valley", "Colombia", "medium", "beans", "Caramel and apple", 19.0),
        (3, "Antigua Sunrise", "antigua-sunrise", "Guatemala", "medium-dark", "beans", "Chocolate and spice", 20.0),
        (4, "Nyeri AA", "nyeri-aa", "Kenya", "light-medium", "beans", "Blackcurrant and grapefruit", 24.0),
        (5, "Sumatra Mandheling", "sumatra-mandheling", "Indonesia", "dark", "beans", "Earthy and cedar", 18.0),
        (6, "Decaf Sidamo", "decaf-sidamo", "Ethiopia", "medium", "beans", "Stone fruit and floral", 21.0),
        (7, "House Espresso Blend", "house-espresso-blend", "Multi-origin", "dark", "beans", "Chocolate and cherry", 17.0),
        (8, "Cold Brew Blend", "cold-brew-blend", "Multi-origin", "medium", "beans", "Vanilla and toffee", 16.0),
        (9, "Ceramic Pour-Over Dripper", "ceramic-pour-over-dripper", None, None, "equipment", "Hand-thrown ceramic cone", 35.0),
        (10, "Glass Cold Brew Tower", "glass-cold-brew-tower", None, None, "equipment", "600ml borosilicate glass tower", 65.0),
        (11, "Burr Grinder Pro", "burr-grinder-pro", None, None, "equipment", "40mm conical steel burrs", 89.0),
        (12, "Gooseneck Kettle", "gooseneck-kettle", None, None, "equipment", "1L built-in thermometer", 55.0),
        (13, "Precision Brew Scale", "precision-brew-scale", None, None, "equipment", "0.1g accuracy", 30.0),
        (14, "Reusable Metal Filter", "reusable-metal-filter", None, None, "equipment", "Stainless steel mesh", 15.0),
    ]

    with get_conn() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO users (email, password, name, role) VALUES (?, ?, ?, ?)",
            users,
        )
        conn.executemany(
            """
            INSERT OR IGNORE INTO products
            (id, name, slug, origin, roast_level, category, description, price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            products,
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO orders
            (id, user_email, total, status, billing_address, card_last4, phone)
            VALUES (1, 'demo@singleorigin.example', 59.5, 'DELIVERED', '123 Roast St, SF, CA 94107', '4242', '+1-555-0100')
            """
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO subscriptions
            (id, user_email, plan, frequency, status)
            VALUES (1, 'demo@singleorigin.example', 'Explorer', 'Every 2 weeks', 'ACTIVE')
            """
        )
