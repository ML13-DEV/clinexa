from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.especialidades.config import campos_de, CAMPOS_POR_ESPECIALIDAD
from app.especialidades.analisis_config import analisis_de

router = APIRouter()


@router.get("/especialidades")
def listar_especialidades(user = Depends(get_current_user)):
    """Keys de especialidades conocidas por el catálogo (ver
    app/especialidades/config.py), para el selector del panel owner."""
    return list(CAMPOS_POR_ESPECIALIDAD.keys())


@router.get("/especialidades/campos")
def obtener_campos_especialidad(user = Depends(get_current_user)):
    """Campos clínicos específicos de la especialidad del médico logueado,
    para que el frontend arme el formulario de paciente dinámicamente."""
    return [
        {
            "key": campo.key,
            "label": campo.label,
            "tipo": campo.tipo.value,
            "requerido": campo.requerido,
            "opciones": list(campo.opciones),
        }
        for campo in campos_de(user["especialidad"])
    ]


@router.get("/especialidades/analisis")
def obtener_analisis_especialidad(user = Depends(get_current_user)):
    """Determinaciones de laboratorio/estudios del panel de análisis de la
    especialidad del médico logueado, para armar dinámicamente el form,
    la tabla y el gráfico de evolución en paciente.html."""
    return [
        {
            "key": campo.key,
            "label": campo.label,
            "tipo": campo.tipo.value,
            "unidad": campo.unidad,
        }
        for campo in analisis_de(user["especialidad"])
    ]
