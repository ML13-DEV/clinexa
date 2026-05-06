from pydantic import BaseModel
from datetime import datetime

from typing import Optional

class NotaBase(BaseModel):
    paciente_id: int
    contenido: str
    


class NotaCreate(NotaBase):
    fecha: Optional[datetime] = None


class NotaResponse(NotaBase):
    id: int
    fecha: datetime

    model_config = {
        "from_attributes": True
    }