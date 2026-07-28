from pydantic import BaseModel, Field
from datetime import date

class PacienteBase(BaseModel):
    nombre: str
    apellido: str
    dni: str
    fecha_nacimiento: date
    telefono: str | None = None
    obra_social: str | None = None
    numero_afiliado: str | None = None

    alergias: str | None = None
    medico_cabecera: str | None = None

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

    # Campos específicos de la especialidad del médico (ver
    # app/especialidades/config.py), ej. hematología: sangrados,
    # trombosis, gestas, vacunas, fim_descriptivo.
    datos_clinicos: dict = Field(default_factory=dict)


class PacienteCreate(PacienteBase):
    pass


class PacienteUpdate(BaseModel):
    nombre: str | None = None
    apellido: str | None = None
    dni: str | None = None
    fecha_nacimiento: date | None = None
    telefono: str | None = None
    obra_social: str | None = None
    numero_afiliado: str | None = None

    alergias: str | None = None
    medico_cabecera: str | None = None

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

    datos_clinicos: dict | None = None


class PacienteResponse(PacienteBase):
    id: int
    edad: int
    imc: float | None = None

    model_config = {
        "from_attributes": True
    }
