import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Azure SQL Database or local SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./babylog.db")

if DATABASE_URL.startswith("sqlite"):
    # SQLite requires a specific connect_args setting
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # Assumes other DBs like PostgreSQL, MySQL, or MSSQL
    engine = create_engine(DATABASE_URL)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
