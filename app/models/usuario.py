from enum import Enum

from sqlalchemy import Column, DateTime, Integer, String, func

from app.database import Base


class RolUsuario(str, Enum):
    OWNER = "owner"
    MEDICO = "medico"


class EstadoCuenta(str, Enum):
    """Reemplaza al viejo `activo` booleano: "¿puede loguearse?" es una
    sola pregunta con una sola respuesta, no la combinación de dos campos
    que podrían contradecirse. Pensado para poder sumar estados de la
    Fase B (ej. "aprobado, pendiente de pago") agregando un valor acá,
    sin otra migración de columna.

    - pendiente: se registró solo por /registro, esperando que el owner
      lo apruebe. No puede loguearse.
    - activo: puede loguearse. Default para médicos creados directo por
      el owner (POST /owner/usuarios) — si el owner lo da de alta a
      mano, ya está aprobado por definición.
    - rechazado: el owner rechazó la solicitud de /registro.
    - suspendido: estaba activo, el owner lo desactivó manualmente
      (antes era `activo=False`).
    """

    PENDIENTE = "pendiente"
    ACTIVO = "activo"
    RECHAZADO = "rechazado"
    SUSPENDIDO = "suspendido"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String(100), unique=True, nullable=False)

    password = Column(String(255), nullable=False)

    # Nombre real del médico (ej. "Dra. Ana Pérez"), distinto de
    # `username` (el handle de login). Nullable porque las cuentas
    # creadas antes de este campo no lo tienen; requerido de acá en más
    # tanto en /registro como en el alta manual del owner.
    nombre = Column(String(150), nullable=True)

    # String, no Enum de SQLAlchemy a propósito: un Enum mapea a un tipo
    # ENUM nativo en Postgres y exigiría migrar el tipo de columna. La
    # validación real de valores permitidos ya la hace RolUsuario del
    # lado de Pydantic (ver UsuarioCreate), que es el único lugar donde
    # se escribe este campo.
    rol = Column(String(50), default="medico")

    especialidad = Column(String(100), nullable=True)

    # Ver EstadoCuenta. Mismo criterio que `rol`: String + Enum de
    # Pydantic, no Enum de SQLAlchemy.
    estado = Column(String(50), nullable=False, default="activo")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
