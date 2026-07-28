from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.analisis import Analisis

from app.schemas.analisis import AnalisisCreate, AnalisisUpdate
from app.core.permissions import get_paciente_propio, get_registro_de_paciente_propio
from app.core.dependencies import get_db, get_current_user

router = APIRouter(
    dependencies=[Depends(get_current_user)]
)


@router.post("/analisis")
def crear_analisis(
    data: AnalisisCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    get_paciente_propio(db, data.paciente_id, user["id"])

    nuevo = Analisis(**data.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.get("/analisis/{paciente_id}")
def obtener_analisis(
    paciente_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    get_paciente_propio(db, paciente_id, user["id"])

    return db.query(Analisis)\
        .filter(Analisis.paciente_id == paciente_id)\
        .order_by(Analisis.fecha.desc())\
        .all()


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

    for key, value in data.dict(exclude_unset=True).items():
        setattr(analisis, key, value)

    db.commit()
    db.refresh(analisis)

    return analisis