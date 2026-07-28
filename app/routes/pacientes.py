from fastapi import APIRouter, Depends, Query, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import date

from app.models.paciente import Paciente
from app.models.turnos import Turno
from app.models.nota import Nota
from app.schemas.paciente import PacienteCreate, PacienteUpdate
from app.core.permissions import get_paciente_propio
from app.core.dependencies import get_db, get_current_user
from app.especialidades.config import validar_datos_clinicos

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


# =========================
# UTIL
# =========================

def calcular_edad(fecha_nacimiento):
    today = date.today()
    return today.year - fecha_nacimiento.year - (
        (today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
    )


def calcular_imc(peso, talla):
    """Talla en centímetros, peso en kilogramos. IMC = peso / (talla_m)^2."""
    if not peso or not talla:
        return None
    talla_m = talla / 100
    if talla_m <= 0:
        return None
    return round(peso / (talla_m ** 2), 2)


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

    existente = (
        db.query(Paciente)
        .filter(Paciente.dni == paciente.dni, Paciente.usuario_id == user["id"])
        .first()
    )

    if existente:
        raise HTTPException(status_code=400, detail="DNI ya registrado")

    try:
        validar_datos_clinicos(user["especialidad"], paciente.datos_clinicos)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    nuevo = Paciente(**paciente.dict(), usuario_id=user["id"])
    nuevo.imc = calcular_imc(nuevo.peso, nuevo.talla)

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
    query = db.query(Paciente).filter(Paciente.usuario_id == user["id"])

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
    paciente = get_paciente_propio(db, paciente_id, user["id"])

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
    data: PacienteUpdate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    paciente = get_paciente_propio(db, id, user["id"])

    cambios = data.dict(exclude_unset=True)

    if "dni" in cambios:
        existente = (
            db.query(Paciente)
            .filter(Paciente.dni == cambios["dni"], Paciente.usuario_id == user["id"])
            .first()
        )
        if existente and existente.id != id:
            raise HTTPException(status_code=400, detail="DNI ya registrado")

    if "datos_clinicos" in cambios:
        try:
            validar_datos_clinicos(user["especialidad"], cambios["datos_clinicos"])
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    for key, value in cambios.items():
        setattr(paciente, key, value)

    if "peso" in cambios or "talla" in cambios:
        paciente.imc = calcular_imc(paciente.peso, paciente.talla)

    db.commit()
    db.refresh(paciente)

    return paciente


@router.delete("/pacientes/{id}")
def eliminar_paciente(
    id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    paciente = get_paciente_propio(db, id, user["id"])

    db.delete(paciente)
    db.commit()

    return {"ok": True}