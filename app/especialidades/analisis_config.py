"""Catálogo de determinaciones de laboratorio/estudios por especialidad.

Mismo criterio que app/especialidades/config.py (campos clínicos del
paciente): Python, no tabla — lo da de alta el equipo de desarrollo, no
cambia en runtime. Se separa en su propio módulo porque tiene una forma
distinta (necesita `unidad`) y para no mezclar dos catálogos distintos
en un mismo archivo a medida que crecen.

Cada Analisis (header id, paciente_id, fecha) guarda sus determinaciones
en AnalisisValor (analisis_id, analisis_key, valor), con las keys que
este catálogo define para la especialidad del médico dueño del paciente.
"""

from dataclasses import dataclass
from enum import Enum


class TipoAnalisis(str, Enum):
    NUMERO = "numero"
    TEXTO = "texto"


@dataclass(frozen=True)
class CampoAnalisis:
    key: str
    label: str
    tipo: TipoAnalisis
    unidad: str = ""


ANALISIS_POR_ESPECIALIDAD: dict[str, list[CampoAnalisis]] = {
    "hematologia": [
        CampoAnalisis("gb", "Glóbulos blancos", TipoAnalisis.NUMERO, "x10³/µL"),
        CampoAnalisis("nt", "Neutrófilos", TipoAnalisis.NUMERO, "%"),
        CampoAnalisis("l", "Linfocitos", TipoAnalisis.NUMERO, "%"),
        CampoAnalisis("hb", "Hemoglobina", TipoAnalisis.NUMERO, "g/dL"),
        CampoAnalisis("hto", "Hematocrito", TipoAnalisis.NUMERO, "%"),
        CampoAnalisis("vcm", "VCM", TipoAnalisis.NUMERO, "fL"),
        CampoAnalisis("pqts", "Plaquetas", TipoAnalisis.NUMERO, "x10³/µL"),
        CampoAnalisis("ferremia", "Ferremia", TipoAnalisis.NUMERO, "µg/dL"),
        CampoAnalisis("ferritina", "Ferritina", TipoAnalisis.NUMERO, "ng/mL"),
        CampoAnalisis("saturacion", "% Saturación de transferrina", TipoAnalisis.NUMERO, "%"),
        CampoAnalisis("tibc", "TIBC", TipoAnalisis.NUMERO, "µg/dL"),
        CampoAnalisis("epo", "Eritropoyetina", TipoAnalisis.NUMERO, "mUI/mL"),
        CampoAnalisis("vit_b12", "Vitamina B12", TipoAnalisis.NUMERO, "pg/mL"),
        CampoAnalisis("af", "Ácido fólico", TipoAnalisis.NUMERO, "ng/mL"),
        CampoAnalisis("ldh", "LDH", TipoAnalisis.NUMERO, "U/L"),
        CampoAnalisis("hepatograma", "Hepatograma", TipoAnalisis.TEXTO),
        CampoAnalisis("funcion_renal", "Función renal", TipoAnalisis.TEXTO),
        CampoAnalisis("tp", "Tiempo de protrombina (TP)", TipoAnalisis.NUMERO, "%"),
        CampoAnalisis("kptt", "KPTT", TipoAnalisis.NUMERO, "seg"),
        CampoAnalisis("rino", "RIN", TipoAnalisis.NUMERO),
        CampoAnalisis("otros_analisis", "Otros análisis", TipoAnalisis.TEXTO),
    ],
}


def analisis_de(especialidad: str) -> list[CampoAnalisis]:
    return ANALISIS_POR_ESPECIALIDAD.get(especialidad, [])
