import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Leemos la URL de la base de datos desde las variables de entorno.
# Si no existe (en tu PC), usa SQLite por defecto.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./med.db")

# 2. Ajuste para PostgreSQL (Render/Railway a veces mandan postgres:// y SQLAlchemy pide postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 3. Configuración del Engine
# El check_same_thread solo es necesario para SQLite.
if "sqlite" in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # pool_pre_ping evita errores por conexiones "muertas" que el pooler
    # de Supabase (Supavisor) puede cerrar por inactividad.
    # pool_size/max_overflow chicos porque el Session Pooler ya maneja
    # el pooling real de conexiones hacia Postgres.
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()