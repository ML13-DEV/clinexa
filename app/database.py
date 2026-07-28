from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

DATABASE_URL = settings.database_url

# Ajuste para PostgreSQL (Render/Railway a veces mandan postgres:// y SQLAlchemy pide postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

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

print(f"Conectado a la base de datos: {DATABASE_URL}")
