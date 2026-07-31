from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.especialidades.config import campos_de, CAMPOS_POR_ESPECIALIDAD
from app.especialidades.analisis_config import analisis_de
from app.models.rango_normal import RangoNormal

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
            "computado": campo.computado,
        }
        for campo in analisis_de(user["especialidad"])
    ]


@router.get("/especialidades/analisis/rangos")
def obtener_rangos_normales(
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    """Valores de referencia (min/max) por determinación, para que
    paciente.html coloree resultados fuera de rango. Solo cubre las keys
    que tengan un rango cargado en rangos_normales (ver migrations/); el
    resto queda sin colorear en el frontend."""
    rangos = (
        db.query(RangoNormal)
        .filter(RangoNormal.especialidad == user["especialidad"])
        .all()
    )
    return [
        {"key": r.analisis_key, "valor_min": r.valor_min, "valor_max": r.valor_max}
        for r in rangos
    ]
