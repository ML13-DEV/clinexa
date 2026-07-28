from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from app.database import Base


class RolUsuario(str, Enum):
    OWNER = "owner"
    MEDICO = "medico"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String(100), unique=True, nullable=False)

    password = Column(String(255), nullable=False)

    # String, no Enum de SQLAlchemy a propósito: un Enum mapea a un tipo
    # ENUM nativo en Postgres y exigiría migrar el tipo de columna. La
    # validación real de valores permitidos ya la hace RolUsuario del
    # lado de Pydantic (ver UsuarioCreate), que es el único lugar donde
    # se escribe este campo.
    rol = Column(String(50), default="medico")

    especialidad = Column(String(100), nullable=True)

    activo = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
