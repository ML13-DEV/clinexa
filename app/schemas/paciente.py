from pydantic import BaseModel
from datetime import date

class PacienteBase(BaseModel):
    nombre: str
    apellido: str
    dni: str
    fecha_nacimiento: date
    telefono: str | None = None
    obra_social: str | None = None
    numero_afiliado: str | None = None

    sangrados: str | None = None
    trombosis: str | None = None
    alergias: str | None = None
    vacunas: str | None = None
    gestas: str | None = None
    medico_cabecera: str | None = None
    fim_descriptivo: str | None = None


class PacienteCreate(PacienteBase):
    pass


class PacienteResponse(PacienteBase):
    id: int
    edad: int

    model_config = {
        "from_attributes": True
    }