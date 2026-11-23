from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Kapcsolódás a Dockerben futó PostgreSQL adatbázishoz
SQLALCHEMY_DATABASE_URL = "postgresql://admin:secretpassword@db:5432/aiproducts"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,         # Hány kapcsolatot tartson fenn egyszerre (alapértelmezett általában 5)
    max_overflow=20,      # Hány extra kapcsolatot engedélyezzen vészhelyzetben
    pool_timeout=30       # Hány másodpercig várjon, ha nincs szabad kapcsolat (timeout)
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Ez a függvény adja majd az adatbázis kapcsolatot az API végpontoknak
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()