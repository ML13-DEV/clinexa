from fastapi import APIRouter, Depends, Query, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from datetime import date, datetime, timedelta

from app.database import SessionLocal
from app.models.paciente import Paciente
from app.models.turnos import Turno
from app.models.nota import Nota
from app.schemas.paciente import PacienteCreate, PacienteUpdate

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


def calcular_imc(peso, talla):
    """Talla en centímetros, peso en kilogramos. IMC = peso / (talla_m)^2."""
    if not peso or not talla:
        return None
    talla_m = talla / 100
    if talla_m <= 0:
        return None
    return round(peso / (talla_m ** 2), 2)


# Rangos etarios fijos para el dashboard de estadísticas.
RANGOS_ETARIOS = [
    ("0-17", 0, 17),
    ("18-30", 18, 30),
    ("31-45", 31, 45),
    ("46-60", 46, 60),
    ("61+", 61, None),
]


def _rango_etario(edad):
    for etiqueta, minimo, maximo in RANGOS_ETARIOS:
        if maximo is None:
            if edad >= minimo:
                return etiqueta
        elif minimo <= edad <= maximo:
            return etiqueta
    return RANGOS_ETARIOS[0][0]


def _top_texto_normalizado(db, columna, limite=5):
    """Agrupa un campo de texto libre ignorando mayúsculas/espacios,
    mostrando la etiqueta con formato prolijo (primera letra de cada
    palabra en mayúscula)."""
    clave = func.trim(func.lower(columna))
    etiqueta = func.initcap(clave)

    filas = (
        db.query(etiqueta.label("label"), func.count().label("cantidad"))
        .filter(columna.isnot(None))
        .filter(func.trim(columna) != "")
        .group_by(clave)
        .order_by(func.count().desc())
        .limit(limite)
        .all()
    )

    return [{"label": label, "cantidad": cantidad} for label, cantidad in filas]


def _distribucion_por_edad(db):
    """Trae solo fecha_nacimiento (no el paciente completo) y reusa
    calcular_edad() para agrupar en rangos fijos."""
    fechas = (
        db.query(Paciente.fecha_nacimiento)
        .filter(Paciente.fecha_nacimiento.isnot(None))
        .all()
    )

    conteos = {etiqueta: 0 for etiqueta, _, _ in RANGOS_ETARIOS}

    for (fecha_nacimiento,) in fechas:
        edad = calcular_edad(fecha_nacimiento)
        conteos[_rango_etario(edad)] += 1

    return [
        {"rango": etiqueta, "cantidad": conteos[etiqueta]}
        for etiqueta, _, _ in RANGOS_ETARIOS
    ]


def _primer_dia_hace_n_meses(n):
    hoy = date.today()
    mes_total = hoy.month - 1 - n
    anio = hoy.year + mes_total // 12
    mes = mes_total % 12 + 1
    return date(anio, mes, 1)


def _pacientes_nuevos_por_mes(db, meses=6):
    mes_trunc = func.date_trunc("month", Paciente.creado_en)
    desde = _primer_dia_hace_n_meses(meses - 1)

    filas = (
        db.query(mes_trunc.label("mes"), func.count().label("cantidad"))
        .filter(Paciente.creado_en >= desde)
        .group_by(mes_trunc)
        .order_by(mes_trunc)
        .all()
    )

    return [{"mes": mes.strftime("%Y-%m"), "cantidad": cantidad} for mes, cantidad in filas]


def _pacientes_sin_seguimiento(db, meses=6):
    """Pacientes sin ninguna nota, o cuya nota mas reciente supera el
    umbral: se 'perdieron' de seguimiento clinico."""
    cutoff = datetime.utcnow() - timedelta(days=30 * meses)

    ultima_nota = (
        db.query(
            Nota.paciente_id.label("paciente_id"),
            func.max(Nota.fecha).label("ultima_fecha"),
        )
        .group_by(Nota.paciente_id)
        .subquery()
    )

    return (
        db.query(func.count(Paciente.id))
        .outerjoin(ultima_nota, ultima_nota.c.paciente_id == Paciente.id)
        .filter(
            or_(
                ultima_nota.c.ultima_fecha.is_(None),
                ultima_nota.c.ultima_fecha < cutoff,
            )
        )
        .scalar()
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


@router.get("/pacientes/estadisticas")
def estadisticas_pacientes(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    return {
        "total_pacientes": db.query(func.count(Paciente.id)).scalar(),
        "top_diagnosticos": _top_texto_normalizado(db, Paciente.diagnostico_principal),
        "top_localidades": _top_texto_normalizado(db, Paciente.localidad),
        "top_obras_sociales": _top_texto_normalizado(db, Paciente.obra_social),
        "rango_etario": _distribucion_por_edad(db),
        "pacientes_nuevos_por_mes": _pacientes_nuevos_por_mes(db),
        "pacientes_sin_seguimiento": _pacientes_sin_seguimiento(db),
    }


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
    data: PacienteUpdate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    paciente = db.query(Paciente).get(id)

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    cambios = data.dict(exclude_unset=True)

    if "dni" in cambios:
        existente = db.query(Paciente).filter(Paciente.dni == cambios["dni"]).first()
        if existente and existente.id != id:
            raise HTTPException(status_code=400, detail="DNI ya registrado")

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

    paciente = db.query(Paciente).get(id)

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    db.delete(paciente)
    db.commit()

    return {"ok": True}