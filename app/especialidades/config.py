"""Catálogo de campos clínicos por especialidad.

Config en Python (no tabla en la base): las especialidades las da de alta
el equipo de desarrollo, no los médicos desde una UI, así que no hace
falta una tabla + CRUD + migración para algo que cambia por deploy, no en
runtime. Si en el futuro un médico necesita agregar sus propios campos
custom, ahí sí vale la pena migrar esto a una tabla `especialidad_campos`.

Cada Paciente guarda sus campos específicos en `datos_clinicos` (JSONB),
con las keys que este catálogo define para la especialidad del médico
dueño del paciente.
"""

from dataclasses import dataclass, field
from enum import Enum


class TipoCampo(str, Enum):
    TEXTO = "texto"
    TEXTAREA = "textarea"
    NUMERO = "numero"
    FECHA = "fecha"
    SELECT = "select"


@dataclass(frozen=True)
class CampoClinico:
    key: str
    label: str
    tipo: TipoCampo
    requerido: bool = False
    opciones: tuple[str, ...] = field(default=())  # solo aplica a tipo SELECT


CAMPOS_POR_ESPECIALIDAD: dict[str, list[CampoClinico]] = {
    "hematologia": [
        CampoClinico("sangrados", "Sangrados", TipoCampo.TEXTAREA),
        CampoClinico("trombosis", "Trombosis", TipoCampo.TEXTAREA),
        CampoClinico("gestas", "Gestas", TipoCampo.TEXTO),
        CampoClinico("vacunas", "Vacunas", TipoCampo.TEXTAREA),
        CampoClinico("fim_descriptivo", "FIM (descriptivo)", TipoCampo.TEXTAREA),
    ],
    "nutricion": [
        CampoClinico("objetivo_peso", "Objetivo de peso (kg)", TipoCampo.NUMERO),
        CampoClinico(
            "actividad_fisica", "Actividad física", TipoCampo.SELECT,
            opciones=("sedentario", "leve", "moderada", "intensa"),
        ),
        CampoClinico("alergias_alimentarias", "Alergias alimentarias", TipoCampo.TEXTAREA),
        CampoClinico("plan_alimentario", "Plan alimentario", TipoCampo.TEXTAREA),
        CampoClinico("suplementacion", "Suplementación", TipoCampo.TEXTAREA),
        CampoClinico(
            "antecedentes_gastrointestinales", "Antecedentes gastrointestinales", TipoCampo.TEXTAREA
        ),
    ],
    "cardiologia": [
        CampoClinico("factores_riesgo_cv", "Factores de riesgo cardiovascular", TipoCampo.TEXTAREA),
        CampoClinico(
            "clase_funcional_nyha", "Clase funcional NYHA", TipoCampo.SELECT,
            opciones=("I", "II", "III", "IV"),
        ),
        CampoClinico(
            "antecedentes_cardiovasculares", "Antecedentes cardiovasculares", TipoCampo.TEXTAREA
        ),
        CampoClinico("ecg_basal", "ECG basal", TipoCampo.TEXTAREA),
        CampoClinico("tratamiento_cardiologico", "Tratamiento cardiológico", TipoCampo.TEXTAREA),
    ],
    "neurologia": [
        CampoClinico("antecedentes_neurologicos", "Antecedentes neurológicos", TipoCampo.TEXTAREA),
        CampoClinico(
            "tipo_cefalea", "Tipo de cefalea", TipoCampo.SELECT,
            opciones=("tensional", "migraña", "cluster", "otra"),
        ),
        CampoClinico("escala_funcional", "Escala funcional (ej. Rankin)", TipoCampo.TEXTO),
        CampoClinico("medicacion_neurologica", "Medicación neurológica", TipoCampo.TEXTAREA),
        CampoClinico("estudios_imagen", "Estudios de imagen", TipoCampo.TEXTAREA),
    ],
}


def campos_de(especialidad: str) -> list[CampoClinico]:
    return CAMPOS_POR_ESPECIALIDAD.get(especialidad, [])


def validar_datos_clinicos(especialidad: str, datos: dict) -> None:
    """Chequea que estén los campos requeridos de la especialidad.

    No valida tipos ni opciones de SELECT todavía: alcanza con esto hasta
    que el formulario dinámico del frontend esté armado y se vea qué tanta
    validación de tipo hace falta del lado del servidor.
    """
    faltantes = [
        campo.label
        for campo in campos_de(especialidad)
        if campo.requerido and not datos.get(campo.key)
    ]
    if faltantes:
        raise ValueError(f"Faltan campos requeridos: {', '.join(faltantes)}")
