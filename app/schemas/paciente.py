from pydantic import BaseModel
from datetime import date

class PacienteBase(BaseModel):
    nombre: str
    apellido: str
    dni: str
    fecha_nacimiento: date
    telefono: str | None = None
    localidad: str | None = None
    obra_social: str | None = None
    numero_afiliado: str | None = None

    sangrados: str | None = None
    trombosis: str | None = None
    alergias: str | None = None
    vacunas: str | None = None
    gestas: str | None = None
    medico_cabecera: str | None = None
    fim_descriptivo: str | None = None

    peso: float | None = None
    talla: float | None = None
    diagnostico_principal: str | None = None
    ocupacion: str | None = None
    habitos: str | None = None
    medicacion_habitual: str | None = None
    cirugias: str | None = None
    transfusiones: str | None = None
    antecedentes_personales: str | None = None
    antecedentes_familiares: str | None = None


class PacienteCreate(PacienteBase):
    pass


class PacienteUpdate(BaseModel):
    nombre: str | None = None
    apellido: str | None = None
    dni: str | None = None
    fecha_nacimiento: date | None = None
    telefono: str | None = None
    localidad: str | None = None
    obra_social: str | None = None
    numero_afiliado: str | None = None

    sangrados: str | None = None
    trombosis: str | None = None
    alergias: str | None = None
    vacunas: str | None = None
    gestas: str | None = None
    medico_cabecera: str | None = None
    fim_descriptivo: str | None = None

    peso: float | None = None
    talla: float | None = None
    diagnostico_principal: str | None = None
    ocupacion: str | None = None
    habitos: str | None = None
    medicacion_habitual: str | None = None
    cirugias: str | None = None
    transfusiones: str | None = None
    antecedentes_personales: str | None = None
    antecedentes_familiares: str | None = None


class PacienteResponse(PacienteBase):
    id: int
    edad: int
    imc: float | None = None

    model_config = {
        "from_attributes": True
    }
