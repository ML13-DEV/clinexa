from datetime import date

from fastapi import APIRouter, Depends, Query, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.models.paciente import Paciente
from app.models.turnos import Turno
from app.models.nota import Nota
from app.schemas.paciente import PacienteCreate, PacienteUpdate
from app.core.permissions import get_paciente_propio
from app.core.dependencies import get_db, get_current_medico
from app.core.timezone import hoy_consultorio
from app.especialidades.config import validar_datos_clinicos

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


# =========================
# UTIL
# =========================

def calcular_edad(fecha_nacimiento):
    today = hoy_consultorio()
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


# Rangos etarios fijos para /pacientes/estadisticas.
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


def _top_texto_normalizado(db, usuario_id, columna, limite=5):
    """Agrupa un campo de texto libre ignorando mayúsculas/espacios
    (TRIM+LOWER, portable a SQLite y Postgres). La etiqueta se muestra en
    Python con .title() sobre las `limite` filas ya agrupadas en SQL —
    evita INITCAP, que no existe en SQLite (los tests corren ahí)."""
    clave = func.trim(func.lower(columna))

    filas = (
        db.query(clave.label("clave"), func.count().label("cantidad"))
        .filter(Paciente.usuario_id == usuario_id)
        .filter(columna.isnot(None))
        .filter(func.trim(columna) != "")
        .group_by(clave)
        .order_by(func.count().desc())
        .limit(limite)
        .all()
    )

    return [{"label": clave.title(), "cantidad": cantidad} for clave, cantidad in filas]


def _distribucion_por_edad(db, usuario_id):
    """Trae solo fecha_nacimiento (no el paciente completo) y reusa
    calcular_edad() para agrupar en rangos fijos."""
    fechas = (
        db.query(Paciente.fecha_nacimiento)
        .filter(Paciente.usuario_id == usuario_id)
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
    hoy = hoy_consultorio()
    mes_total = hoy.month - 1 - n
    anio = hoy.year + mes_total // 12
    mes = mes_total % 12 + 1
    return date(anio, mes, 1)


def _pacientes_nuevos_por_mes(db, usuario_id, meses=6):
    """Agrupa por (año, mes) de created_at con EXTRACT en vez de
    date_trunc/strftime: EXTRACT lo traduce SQLAlchemy a algo válido tanto
    en Postgres como en SQLite (los tests corren ahí), a diferencia de
    date_trunc (solo Postgres) o strftime (solo SQLite)."""
    anio = func.extract("year", Paciente.created_at)
    mes = func.extract("month", Paciente.created_at)
    desde = _primer_dia_hace_n_meses(meses - 1)

    filas = (
        db.query(anio.label("anio"), mes.label("mes"), func.count().label("cantidad"))
        .filter(Paciente.usuario_id == usuario_id)
        .filter(Paciente.created_at >= desde)
        .group_by(anio, mes)
        .order_by(anio, mes)
        .all()
    )

    return [
        {"mes": f"{int(anio):04d}-{int(mes):02d}", "cantidad": cantidad}
        for anio, mes, cantidad in filas
    ]


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
    user = Depends(get_current_medico)
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
        raise HTTPException(status_code=422, detail=str(e))

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
    user = Depends(get_current_medico)
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


@router.get("/pacientes/estadisticas")
def obtener_estadisticas_pacientes(
    db: Session = Depends(get_db),
    user = Depends(get_current_medico)
):
    """Estadisticas de los propios pacientes del medico logueado (no
    confundir con /owner/estadisticas, que es a nivel plataforma). Todo
    via COUNT/GROUP BY filtrado por usuario_id, salvo el rango etario que
    trae solo fecha_nacimiento y bucketiza en Python reusando
    calcular_edad()."""

    total_pacientes = (
        db.query(func.count(Paciente.id))
        .filter(Paciente.usuario_id == user["id"])
        .scalar()
    )

    return {
        "total_pacientes": total_pacientes,
        "top_diagnosticos": _top_texto_normalizado(
            db, user["id"], Paciente.diagnostico_principal
        ),
        "top_localidades": _top_texto_normalizado(
            db, user["id"], Paciente.localidad
        ),
        "top_obras_sociales": _top_texto_normalizado(
            db, user["id"], Paciente.obra_social
        ),
        "rango_etario": _distribucion_por_edad(db, user["id"]),
        "pacientes_nuevos_por_mes": _pacientes_nuevos_por_mes(db, user["id"]),
    }


@router.get("/pacientes/{paciente_id}")
def obtener_paciente(
    paciente_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_medico)
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
    user = Depends(get_current_medico)
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
            raise HTTPException(status_code=422, detail=str(e))

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
    user = Depends(get_current_medico)
):

    paciente = get_paciente_propio(db, id, user["id"])

    db.delete(paciente)
    db.commit()

    return {"ok": True}