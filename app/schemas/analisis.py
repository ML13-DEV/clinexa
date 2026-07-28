from pydantic import BaseModel
from datetime import date, datetime

class AnalisisCreate(BaseModel):
    paciente_id: int
    fecha: date

    gb: float | None = None
    nt: float | None = None
    l: float | None = None
    hb: float | None = None
    hto: float | None = None
    vcm: float | None = None
    pqts: float | None = None

    ferremia: float | None = None
    ferritina: float | None = None
    saturacion: float | None = None
    tibc: float | None = None

    epo: float | None = None
    vit_b12: float | None = None
    af: float | None = None
    ldh: float | None = None

    hepatograma: str | None = None
    funcion_renal: str | None = None

    tp: float | None = None
    kptt: float | None = None
    rino: float | None = None

    otros_analisis: str | None = None


class AnalisisUpdate(BaseModel):
    fecha: datetime | None = None
    gb: float | None = None
    nt: float | None = None
    l: float | None = None
    hb: float | None = None
    hto: float | None = None
    vcm: float | None = None
    pqts: float | None = None

    ferremia: float | None = None
    ferritina: float | None = None
    saturacion: float | None = None
    tibc: float | None = None

    epo: float | None = None
    vit_b12: float | None = None
    af: float | None = None
    ldh: float | None = None

    hepatograma: str | None = None
    funcion_renal: str | None = None

    tp: float | None = None
    kptt: float | None = None
    rino: float | None = None

    otros_analisis: str | None = None