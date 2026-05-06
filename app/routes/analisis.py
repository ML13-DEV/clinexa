from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.analisis import Analisis

from app.schemas.analisis import AnalisisCreate, AnalisisUpdate
from app.auth import get_current_user  # 👈 agregado

router = APIRouter(
    dependencies=[Depends(get_current_user)]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/analisis")
def crear_analisis(
    data: AnalisisCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)  # 👈 agregado
):
    nuevo = Analisis(**data.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.get("/analisis/{paciente_id}")
def obtener_analisis(
    paciente_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)  # 👈 agregado
):
    return db.query(Analisis)\
        .filter(Analisis.paciente_id == paciente_id)\
        .order_by(Analisis.fecha.desc())\
        .all()


@router.delete("/analisis/{id}")
def eliminar_analisis(
    id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)  # 👈 agregado
):
    analisis = db.query(Analisis).filter(Analisis.id == id).first()

    if not analisis:
        raise HTTPException(status_code=404, detail="No existe")

    db.delete(analisis)
    db.commit()

    return {"message": "Eliminado"}


@router.put("/analisis/{id}")
def actualizar_analisis(
    id: int,
    data: AnalisisUpdate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)  # 👈 agregado
):
    analisis = db.query(Analisis).get(id)

    if not analisis:
        raise HTTPException(status_code=404, detail="No encontrado")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(analisis, key, value)

    db.commit()
    db.refresh(analisis)

    return analisis