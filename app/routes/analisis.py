from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.analisis import Analisis, AnalisisValor

from app.schemas.analisis import AnalisisCreate, AnalisisUpdate
from app.core.permissions import get_paciente_propio, get_registro_de_paciente_propio
from app.core.dependencies import get_db, get_current_user

router = APIRouter(
    dependencies=[Depends(get_current_user)]
)

def _serializar(db: Session, analisis: Analisis) -> dict:
    """Aplana las filas de analisis_valores de vuelta a un dict plano
    (mismo shape que el AnalisisCreate/Update), agnóstico de qué
    especialidad/catálogo generó esas keys. Un valor se devuelve como
    float si castea limpio; si no (texto libre: hepatograma, otros_analisis,
    observaciones, ...), se devuelve tal cual."""
    filas = db.query(AnalisisValor).filter(AnalisisValor.analisis_id == analisis.id).all()

    resultado = {"id": analisis.id, "paciente_id": analisis.paciente_id, "fecha": analisis.fecha}

    for fila in filas:
        if fila.valor is None:
            resultado[fila.analisis_key] = fila.valor
            continue
        try:
            resultado[fila.analisis_key] = float(fila.valor)
        except ValueError:
            resultado[fila.analisis_key] = fila.valor

    return resultado


def _crear_valores(db: Session, analisis_id: int, datos: dict) -> None:
    for key, valor in datos.items():
        if valor is not None:
            db.add(AnalisisValor(analisis_id=analisis_id, analisis_key=key, valor=str(valor)))


def _actualizar_valores(db: Session, analisis_id: int, datos: dict) -> None:
    existentes = {
        v.analisis_key: v
        for v in db.query(AnalisisValor).filter(AnalisisValor.analisis_id == analisis_id)
    }
    for key, valor in datos.items():
        if valor is None:
            if key in existentes:
                db.delete(existentes[key])
        elif key in existentes:
            existentes[key].valor = str(valor)
        else:
            db.add(AnalisisValor(analisis_id=analisis_id, analisis_key=key, valor=str(valor)))


@router.post("/analisis")
def crear_analisis(
    data: AnalisisCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    get_paciente_propio(db, data.paciente_id, user["id"])

    payload = data.dict()
    paciente_id = payload.pop("paciente_id")
    fecha = payload.pop("fecha")

    nuevo = Analisis(paciente_id=paciente_id, fecha=fecha)
    db.add(nuevo)
    db.flush()

    _crear_valores(db, nuevo.id, payload)

    db.commit()
    db.refresh(nuevo)
    return _serializar(db, nuevo)


@router.get("/analisis/{paciente_id}")
def obtener_analisis(
    paciente_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    get_paciente_propio(db, paciente_id, user["id"])

    analisis = (
        db.query(Analisis)
        .filter(Analisis.paciente_id == paciente_id)
        .order_by(Analisis.fecha.desc())
        .all()
    )
    return [_serializar(db, a) for a in analisis]


@router.delete("/analisis/{id}")
def eliminar_analisis(
    id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    analisis = get_registro_de_paciente_propio(db, Analisis, id, user["id"], detail="No existe")

    db.delete(analisis)
    db.commit()

    return {"message": "Eliminado"}


@router.put("/analisis/{id}")
def actualizar_analisis(
    id: int,
    data: AnalisisUpdate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    analisis = get_registro_de_paciente_propio(db, Analisis, id, user["id"], detail="No encontrado")

    cambios = data.dict(exclude_unset=True)
    if "fecha" in cambios:
        analisis.fecha = cambios.pop("fecha")

    _actualizar_valores(db, analisis.id, cambios)

    db.commit()
    db.refresh(analisis)
    return _serializar(db, analisis)
