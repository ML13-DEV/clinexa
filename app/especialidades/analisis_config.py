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
from typing import Callable


class TipoAnalisis(str, Enum):
    NUMERO = "numero"
    TEXTO = "texto"


@dataclass(frozen=True)
class CampoAnalisis:
    key: str
    label: str
    tipo: TipoAnalisis
    unidad: str = ""
    # Campo que no se carga a mano: se recalcula en el backend a partir de
    # otros valores del mismo análisis (ver CALCULOS_COMPUTADOS más abajo).
    # El frontend lo muestra como columna/gráfico pero no como input
    # editable, ni en el form de alta ni en la edición inline de la tabla.
    computado: bool = False


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
        # Métricas de consulta (antropometría): se cargan en cada visita,
        # a diferencia de Paciente.peso/talla que son del alta del
        # paciente (peso inicial, una sola vez). Alimentan el gráfico de
        # evolución igual que cualquier otro campo de este catálogo.
        CampoAnalisis("peso", "Peso", TipoAnalisis.NUMERO, "kg"),
        CampoAnalisis("circunferencia_cintura", "Circunferencia de cintura", TipoAnalisis.NUMERO, "cm"),
        CampoAnalisis("circunferencia_cadera", "Circunferencia de cadera", TipoAnalisis.NUMERO, "cm"),
        CampoAnalisis(
            "indice_cintura_cadera", "Índice cintura-cadera", TipoAnalisis.NUMERO,
            computado=True,
        ),
        CampoAnalisis("porcentaje_grasa_corporal", "% de grasa corporal", TipoAnalisis.NUMERO, "%"),
        CampoAnalisis("porcentaje_masa_muscular", "% de masa muscular", TipoAnalisis.NUMERO, "%"),
        # Determinaciones de laboratorio
        CampoAnalisis("glucemia", "Glucemia", TipoAnalisis.NUMERO, "mg/dL"),
        CampoAnalisis("colesterol_total", "Colesterol total", TipoAnalisis.NUMERO, "mg/dL"),
        CampoAnalisis("hdl", "HDL", TipoAnalisis.NUMERO, "mg/dL"),
        CampoAnalisis("ldl", "LDL", TipoAnalisis.NUMERO, "mg/dL"),
        CampoAnalisis("trigliceridos", "Triglicéridos", TipoAnalisis.NUMERO, "mg/dL"),
        CampoAnalisis("hba1c", "Hemoglobina glicosilada (HbA1c)", TipoAnalisis.NUMERO, "%"),
        CampoAnalisis("albumina", "Albúmina", TipoAnalisis.NUMERO, "g/dL"),
        CampoAnalisis("vitamina_d", "Vitamina D", TipoAnalisis.NUMERO, "ng/mL"),
        CampoAnalisis("otras_metricas", "Otras métricas", TipoAnalisis.TEXTO),
        CampoAnalisis("observaciones", "Observaciones", TipoAnalisis.TEXTO),
    ],
    "cardiologia": [
        CampoAnalisis("peso", "Peso", TipoAnalisis.NUMERO, "kg"),
        CampoAnalisis("colesterol_total", "Colesterol total", TipoAnalisis.NUMERO, "mg/dL"),
        CampoAnalisis("hdl", "HDL", TipoAnalisis.NUMERO, "mg/dL"),
        CampoAnalisis("ldl", "LDL", TipoAnalisis.NUMERO, "mg/dL"),
        CampoAnalisis("trigliceridos", "Triglicéridos", TipoAnalisis.NUMERO, "mg/dL"),
        CampoAnalisis("troponina", "Troponina", TipoAnalisis.NUMERO, "ng/mL"),
        CampoAnalisis("bnp", "BNP", TipoAnalisis.NUMERO, "pg/mL"),
        CampoAnalisis("presion_sistolica", "Presión sistólica", TipoAnalisis.NUMERO, "mmHg"),
        CampoAnalisis("presion_diastolica", "Presión diastólica", TipoAnalisis.NUMERO, "mmHg"),
        CampoAnalisis("frecuencia_cardiaca", "Frecuencia cardíaca", TipoAnalisis.NUMERO, "lpm"),
        CampoAnalisis("saturacion_oxigeno", "Saturación de oxígeno", TipoAnalisis.NUMERO, "%"),
        CampoAnalisis("ecg_hallazgos", "Hallazgos de ECG", TipoAnalisis.TEXTO),
        CampoAnalisis("observaciones", "Observaciones", TipoAnalisis.TEXTO),
    ],
    "neurologia": [
        CampoAnalisis("vitamina_b12", "Vitamina B12", TipoAnalisis.NUMERO, "pg/mL"),
        CampoAnalisis("acido_folico", "Ácido fólico", TipoAnalisis.NUMERO, "ng/mL"),
        CampoAnalisis("tsh", "TSH", TipoAnalisis.NUMERO, "µUI/mL"),
        CampoAnalisis("escala_dolor", "Escala de dolor (0-10)", TipoAnalisis.NUMERO),
        CampoAnalisis("frecuencia_episodios", "Frecuencia de episodios", TipoAnalisis.NUMERO, "por mes"),
        CampoAnalisis("puntaje_cognitivo", "Puntaje cognitivo (ej. MMSE)", TipoAnalisis.NUMERO),
        CampoAnalisis("hallazgos_imagen", "Hallazgos de imagen", TipoAnalisis.TEXTO),
        CampoAnalisis("observaciones", "Observaciones", TipoAnalisis.TEXTO),
    ],
}


def analisis_de(especialidad: str) -> list[CampoAnalisis]:
    return ANALISIS_POR_ESPECIALIDAD.get(especialidad, [])


def _calcular_indice_cintura_cadera(valores: dict) -> float | None:
    cintura = valores.get("circunferencia_cintura")
    cadera = valores.get("circunferencia_cadera")
    if cintura in (None, "") or cadera in (None, ""):
        return None
    try:
        cintura_f = float(cintura)
        cadera_f = float(cadera)
    except (TypeError, ValueError):
        return None
    if cadera_f == 0:
        return None
    return round(cintura_f / cadera_f, 2)


# Funciones de cálculo para los campos marcados computado=True en el
# catálogo de arriba, indexadas por especialidad y key. Cada función
# recibe el dict de valores YA MERGEADO (existentes + cambios de este
# request) y devuelve el nuevo valor computado, o None si no hay
# suficiente información para calcularlo.
CALCULOS_COMPUTADOS: dict[str, dict[str, Callable[[dict], float | None]]] = {
    "nutricion": {
        "indice_cintura_cadera": _calcular_indice_cintura_cadera,
    },
}


def campos_computados(especialidad: str) -> set[str]:
    return {campo.key for campo in analisis_de(especialidad) if campo.computado}


def recalcular_computados(especialidad: str, valores: dict) -> dict:
    """Recalcula los campos computado=True de la especialidad a partir del
    resto de `valores` (que debe ser la vista ya mergeada: lo que ya
    estaba guardado + los cambios de este request). Devuelve un dict
    listo para pisar en el payload a persistir -- incluye None cuando no
    hay datos suficientes, para que se borre el valor viejo si ya no
    corresponde."""
    return {
        key: funcion(valores)
        for key, funcion in CALCULOS_COMPUTADOS.get(especialidad, {}).items()
    }


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
