import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Leemos la URL de la base de datos desde las variables de entorno.
# Si no existe (en tu PC), usa SQLite por defecto.
#DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./med.db")
DATABASE_URL = "sqlite:///./med.db"

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1
    )
print("DATABASE_URL =", DATABASE_URL)

# 2. Ajuste para PostgreSQL (Render/Railway a veces mandan postgres:// y SQLAlchemy pide postgresql://)
#if DATABASE_URL.startswith("postgres://"):
 #   DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 3. Configuración del Engine
# El check_same_thread solo es necesario para SQLite.
if "sqlite" in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()