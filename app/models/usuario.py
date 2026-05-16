from sqlalchemy import Boolean, Column, Integer, String

from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String(100), unique=True, nullable=False)

    password = Column(String(255), nullable=False)

    rol = Column(String(50), default="medico")

    especialidad = Column(String(100), nullable=True)

    activo = Column(Boolean, default=True)