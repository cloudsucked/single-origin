from app.db import init_db, seed_db


if __name__ == "__main__":
    init_db()
    seed_db()
    print("Database seeded.")
