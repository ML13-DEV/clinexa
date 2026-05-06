from typing import Optional

from pydantic import BaseModel
from datetime import datetime

class TurnoBase(BaseModel):
    paciente_id: Optional[int] = None
    fecha: datetime
    nombre_temp: Optional[str] = None
    motivo: str
    diagnostico: str | None = None
    observaciones: str | None = None


class TurnoCreate(TurnoBase):
    pass


class TurnoResponse(TurnoBase):
    paciente_id: Optional[int] = None
    fecha: datetime
    nombre_temp: Optional[str] = None
    motivo: str
    diagnostico: str | None = None
    observaciones: str | None = None

    model_config = {
        "from_attributes": True
    }