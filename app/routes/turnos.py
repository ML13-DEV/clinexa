from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from datetime import datetime
from pydantic import BaseModel

from app.models.paciente import Paciente
from app.models.turnos import Turno
from app.schemas.turnos import TurnoCreate

from app.core.permissions import get_paciente_propio
from app.core.dependencies import get_db, get_current_user, get_current_medico
from app.core.timezone import hoy_consultorio, ahora_consultorio

router = APIRouter(
    dependencies=[Depends(get_current_medico)]
)

# =========================
# CREAR TURNO
# =========================

@router.post("/turnos")
def crear_turno(
    turno: TurnoCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    if not turno.paciente_id and not turno.nombre_temp:
        raise HTTPException(status_code=400, detail="Falta paciente o nombre")

    if turno.paciente_id:
        get_paciente_propio(db, turno.paciente_id, user["id"])

    existente = db.query(Turno).filter(
        Turno.usuario_id == user["id"],
        Turno.fecha == turno.fecha,
        Turno.estado == "pendiente"
    ).first()

    if existente:
        raise HTTPException(status_code=400, detail="Ya existe un turno en ese horario")

    nuevo = Turno(**turno.dict(), usuario_id=user["id"])
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return nuevo

# =========================
# ATENDER TURNO
# =========================

class AtenderTurno(BaseModel):
    diagnostico: str | None = None
    observaciones: str | None = None

@router.put("/turnos/{turno_id}/atender")
def marcar_atendido(
    turno_id: int,
    data: AtenderTurno,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    turno = db.query(Turno).filter(Turno.id == turno_id, Turno.usuario_id == user["id"]).first()

    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    turno.estado = "atendido"
    turno.diagnostico = data.diagnostico
    turno.observaciones = data.observaciones

    db.commit()
    db.refresh(turno)

    return turno

# =========================
# EDITAR TURNO
# =========================

class TurnoUpdate(BaseModel):
    fecha: datetime
    motivo: str
    estado: str
    diagnostico: Optional[str] = None
    observaciones: Optional[str] = None

@router.put("/turnos/{id}")
def actualizar_turno(
    id: int,
    turno: TurnoUpdate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    db_turno = db.query(Turno).filter(Turno.id == id, Turno.usuario_id == user["id"]).first()

    if not db_turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    db_turno.fecha = turno.fecha
    db_turno.motivo = turno.motivo
    db_turno.estado = turno.estado
    db_turno.diagnostico = turno.diagnostico
    db_turno.observaciones = turno.observaciones

    db.commit()
    db.refresh(db_turno)

    return db_turno

# =========================
# ELIMINAR
# =========================

@router.delete("/turnos/{id}")
def eliminar_turno(
    id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    turno = db.query(Turno).filter(Turno.id == id, Turno.usuario_id == user["id"]).first()

    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    db.delete(turno)
    db.commit()

    return {"ok": True}

# =========================
# TURNOS RECIENTES (turnos ya pasados, el mas cercano a ahora primero)
# =========================

@router.get("/turnos/recientes")
def obtener_turnos_recientes(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=5, ge=1, le=50),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    turnos = (
        db.query(Turno)
        .options(joinedload(Turno.paciente))
        .filter(Turno.usuario_id == user["id"], Turno.fecha <= ahora_consultorio())
        .order_by(Turno.fecha.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": t.id,
            "fecha": t.fecha,
            "motivo": t.motivo,
            "estado": t.estado,
            "paciente_id": t.paciente_id,
            "nombre_temp": t.nombre_temp,
            "paciente": {
                "nombre": t.paciente.nombre,
                "apellido": t.paciente.apellido
            } if t.paciente else None
        }
        for t in turnos
    ]

# =========================
# TURNOS HOY
# =========================

@router.get("/turnos/hoy")
def turnos_de_hoy(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    hoy = hoy_consultorio()

    turnos = (
        db.query(Turno)
        .options(joinedload(Turno.paciente))
        .filter(Turno.usuario_id == user["id"], func.date(Turno.fecha) == hoy)
        .order_by(Turno.fecha.asc())
        .all()
    )

    return turnos

# =========================
# STATS
# =========================

@router.get("/turnos/stats")
def estadisticas_turnos(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    hoy = hoy_consultorio()

    total = db.query(func.count(Turno.id))\
        .filter(Turno.usuario_id == user["id"], func.date(Turno.fecha) == hoy)\
        .scalar()

    pendientes = db.query(func.count(Turno.id))\
        .filter(Turno.usuario_id == user["id"], func.date(Turno.fecha) == hoy, Turno.estado == "pendiente")\
        .scalar()

    atendidos = db.query(func.count(Turno.id))\
        .filter(Turno.usuario_id == user["id"], func.date(Turno.fecha) == hoy, Turno.estado == "atendido")\
        .scalar()

    return {
        "total": total,
        "pendientes": pendientes,
        "atendidos": atendidos
    }

# =========================
# TURNOS POR FECHA (AGENDA)
# =========================

@router.get("/turnos/fecha")
def turnos_por_fecha(
    fecha: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    turnos = (
        db.query(Turno)
        .options(joinedload(Turno.paciente))
        .filter(Turno.usuario_id == user["id"], func.date(Turno.fecha) == fecha)
        .order_by(Turno.fecha.asc())
        .all()
    )

    return [
        {
            "id": t.id,
            "fecha": t.fecha,
            "motivo": t.motivo,
            "estado": t.estado,
            "paciente_id": t.paciente_id,
            "nombre_temp": t.nombre_temp,
            "diagnostico": t.diagnostico,
            "observaciones": t.observaciones,
            "paciente": {
                "nombre": t.paciente.nombre,
                "apellido": t.paciente.apellido
            } if t.paciente else None
        }
        for t in turnos
    ]


@router.get("/turnos/buscar")
def buscar_turnos(
    q: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    resultados = (
        db.query(Turno)
        .outerjoin(Paciente)
        .filter(
            Turno.usuario_id == user["id"],
            or_(
                Paciente.nombre.ilike(f"%{q}%"),
                Paciente.apellido.ilike(f"%{q}%"),
                Turno.motivo.ilike(f"%{q}%"),
                Turno.diagnostico.ilike(f"%{q}%"),
                Turno.observaciones.ilike(f"%{q}%"),
                Turno.nombre_temp.ilike(f"%{q}%")
            )
        )
        .all()
    )

    return resultados
