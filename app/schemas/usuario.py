from pydantic import BaseModel

class LoginSchema(BaseModel):
    username: str
    password: str
    
class UsuarioCreate(BaseModel):
    username: str
    password: str
    rol: str
    especialidad: str | None = None


class UsuarioOut(BaseModel):
    id: int
    username: str
    rol: str
    especialidad: str | None = None
    activo: bool

    class Config:
        from_attributes = True