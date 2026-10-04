from app.db import SessionLocal
from app.seed.seed import seed

if __name__ == "__main__":
    with SessionLocal() as session:
        created = seed(session)
    print(f"Seed done: {created}")
