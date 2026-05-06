from fastapi import APIRouter, Depends, Query, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import date

from app.database import SessionLocal
from app.models.paciente import Paciente
from app.models.turnos import Turno
from app.models.nota import Nota
from app.schemas.analisis import AnalisisUpdate
from app.schemas.paciente import PacienteCreate

from app.auth import get_current_user

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


# =========================
# DB
# =========================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# UTIL
# =========================

def calcular_edad(fecha_nacimiento):
    today = date.today()
    return today.year - fecha_nacimiento.year - (
        (today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
    )


# =========================
# VISTA HTML (MUY IMPORTANTE ARRIBA)
# =========================

@router.get("/pacientes/nuevo", response_class=HTMLResponse)
def nuevo_paciente(
    request: Request):
    return templates.TemplateResponse(
        request=request,
        name="nuevo_paciente.html"
    )

# =========================
# CRUD
# =========================

@router.post("/pacientes")
def crear_paciente(
    paciente: PacienteCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    existente = db.query(Paciente).filter(Paciente.dni == paciente.dni).first()

    if existente:
        raise HTTPException(status_code=400, detail="DNI ya registrado")

    nuevo = Paciente(**paciente.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return nuevo


@router.get("/pacientes")
def listar_pacientes(
    search: str = Query(default=None),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    query = db.query(Paciente)

    if search:
        query = query.filter(
            or_(
                Paciente.nombre.ilike(f"%{search}%"),
                Paciente.apellido.ilike(f"%{search}%"),
                Paciente.dni.ilike(f"%{search}%")
            )
        )

    pacientes = query.order_by(Paciente.id.desc()).all()

    return pacientes


@router.get("/pacientes/{paciente_id}")
def obtener_paciente(
    paciente_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    turnos = (
        db.query(Turno)
        .filter(Turno.paciente_id == paciente_id)
        .order_by(Turno.fecha.desc())
        .all()
    )

    notas = (
        db.query(Nota)
        .filter(Nota.paciente_id == paciente_id)
        .order_by(Nota.fecha.desc())
        .all()
    )

    return {
        "paciente": paciente,
        "edad": calcular_edad(paciente.fecha_nacimiento),
        "turnos": turnos,
        "notas": notas,
    }


@router.put("/pacientes/{id}")
def actualizar_paciente(
    id: int,
    data: AnalisisUpdate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    paciente = db.query(Paciente).get(id)

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    if "dni" in data:
        existente = db.query(Paciente).filter(Paciente.dni == data["dni"]).first()
        if existente and existente.id != id:
            raise HTTPException(status_code=400, detail="DNI ya registrado")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(paciente, key, value)

    db.commit()
    db.refresh(paciente)

    return paciente


@router.delete("/pacientes/{id}")
def eliminar_paciente(
    id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    paciente = db.query(Paciente).get(id)

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    db.delete(paciente)
    db.commit()

    return {"ok": True}