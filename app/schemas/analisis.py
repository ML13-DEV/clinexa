from pydantic import BaseModel, ConfigDict
from datetime import date, datetime


class AnalisisCreate(BaseModel):
    """Las determinaciones (gb, hb, glucemia, ...) no son campos fijos:
    varían según el catálogo de la especialidad del médico dueño (ver
    app/especialidades/analisis_config.py), así que se aceptan como
    campos extra en vez de declararlos uno por uno."""

    model_config = ConfigDict(extra="allow")

    paciente_id: int
    fecha: date


class AnalisisUpdate(BaseModel):
    model_config = ConfigDict(extra="allow")

    fecha: datetime | None = None
