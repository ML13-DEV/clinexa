from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.especialidades.config import campos_de

router = APIRouter()


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
