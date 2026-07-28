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
    "nutricion": [
        CampoAnalisis("glucemia", "Glucemia", TipoAnalisis.NUMERO, "mg/dL"),
        CampoAnalisis("colesterol_total", "Colesterol total", TipoAnalisis.NUMERO, "mg/dL"),
        CampoAnalisis("hdl", "HDL", TipoAnalisis.NUMERO, "mg/dL"),
        CampoAnalisis("ldl", "LDL", TipoAnalisis.NUMERO, "mg/dL"),
        CampoAnalisis("trigliceridos", "Triglicéridos", TipoAnalisis.NUMERO, "mg/dL"),
        CampoAnalisis("hba1c", "Hemoglobina glicosilada (HbA1c)", TipoAnalisis.NUMERO, "%"),
        CampoAnalisis("albumina", "Albúmina", TipoAnalisis.NUMERO, "g/dL"),
        CampoAnalisis("vitamina_d", "Vitamina D", TipoAnalisis.NUMERO, "ng/mL"),
        CampoAnalisis("circunferencia_cintura", "Circunferencia de cintura", TipoAnalisis.NUMERO, "cm"),
        CampoAnalisis("observaciones", "Observaciones", TipoAnalisis.TEXTO),
    ],
    "cardiologia": [
        CampoAnalisis("colesterol_total", "Colesterol total", TipoAnalisis.NUMERO, "mg/dL"),
        CampoAnalisis("hdl", "HDL", TipoAnalisis.NUMERO, "mg/dL"),
        CampoAnalisis("ldl", "LDL", TipoAnalisis.NUMERO, "mg/dL"),
        CampoAnalisis("trigliceridos", "Triglicéridos", TipoAnalisis.NUMERO, "mg/dL"),
        CampoAnalisis("troponina", "Troponina", TipoAnalisis.NUMERO, "ng/mL"),
        CampoAnalisis("bnp", "BNP", TipoAnalisis.NUMERO, "pg/mL"),
        CampoAnalisis("presion_sistolica", "Presión sistólica", TipoAnalisis.NUMERO, "mmHg"),
        CampoAnalisis("presion_diastolica", "Presión diastólica", TipoAnalisis.NUMERO, "mmHg"),
        CampoAnalisis("frecuencia_cardiaca", "Frecuencia cardíaca", TipoAnalisis.NUMERO, "lpm"),
        CampoAnalisis("ecg_hallazgos", "Hallazgos de ECG", TipoAnalisis.TEXTO),
        CampoAnalisis("observaciones", "Observaciones", TipoAnalisis.TEXTO),
    ],
    "neurologia": [
        CampoAnalisis("vitamina_b12", "Vitamina B12", TipoAnalisis.NUMERO, "pg/mL"),
        CampoAnalisis("acido_folico", "Ácido fólico", TipoAnalisis.NUMERO, "ng/mL"),
        CampoAnalisis("tsh", "TSH", TipoAnalisis.NUMERO, "µUI/mL"),
        CampoAnalisis("escala_dolor", "Escala de dolor (0-10)", TipoAnalisis.NUMERO),
        CampoAnalisis("hallazgos_imagen", "Hallazgos de imagen", TipoAnalisis.TEXTO),
        CampoAnalisis("observaciones", "Observaciones", TipoAnalisis.TEXTO),
    ],
}


def analisis_de(especialidad: str) -> list[CampoAnalisis]:
    return ANALISIS_POR_ESPECIALIDAD.get(especialidad, [])


def validar_analisis(especialidad: str, datos: dict) -> None:
    """Valida las determinaciones de un análisis contra el catálogo de la
    especialidad: rechaza keys que el catálogo no define y chequea que un
    campo NUMERO castee a float. No hay concepto de "requerido" acá (a
    diferencia de CampoClinico) porque un análisis puede cargar solo
    algunas determinaciones — encaja con que AnalisisUpdate sea parcial.
    """
    catalogo = {campo.key: campo for campo in analisis_de(especialidad)}
    errores = []

    desconocidas = [key for key in datos if key not in catalogo]
    if desconocidas:
        errores.append(
            f"Determinaciones no válidas para {especialidad}: {', '.join(desconocidas)}"
        )

    for key, valor in datos.items():
        campo = catalogo.get(key)
        if campo is None or valor is None:
            continue
        if campo.tipo == TipoAnalisis.NUMERO:
            try:
                float(valor)
            except (TypeError, ValueError):
                errores.append(f"{campo.label}: se esperaba un número, se recibió {valor!r}")

    if errores:
        raise ValueError("; ".join(errores))
