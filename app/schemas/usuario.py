from pydantic import BaseModel

from app.models.usuario import EstadoCuenta, RolUsuario

class LoginSchema(BaseModel):
    username: str
    password: str

class UsuarioCreate(BaseModel):
    nombre: str
    username: str
    password: str
    rol: RolUsuario
    especialidad: str | None = None


class UsuarioUpdate(BaseModel):
    especialidad: str | None = None
    estado: EstadoCuenta | None = None


class UsuarioOut(BaseModel):
    id: int
    nombre: str | None = None
    username: str
    rol: str
    especialidad: str | None = None
    estado: str
    cantidad_pacientes: int = 0

    class Config:
        from_attributes = True


class RegistroCreate(BaseModel):
    """Alta pública vía /registro. `rol` no es un campo acá a propósito:
    se fuerza a "medico" del lado del servidor, nunca se confía en el
    cliente para asignar rol en un endpoint sin autenticación."""

    nombre: str
    username: str
    password: str
    especialidad: str
