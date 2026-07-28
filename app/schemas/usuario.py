from pydantic import BaseModel

from app.models.usuario import RolUsuario

class LoginSchema(BaseModel):
    username: str
    password: str

class UsuarioCreate(BaseModel):
    username: str
    password: str
    rol: RolUsuario
    especialidad: str | None = None


class UsuarioUpdate(BaseModel):
    especialidad: str | None = None
    activo: bool | None = None


class UsuarioOut(BaseModel):
    id: int
    username: str
    rol: str
    especialidad: str | None = None
    activo: bool
    cantidad_pacientes: int = 0

    class Config:
        from_attributes = True