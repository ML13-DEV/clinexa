from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_owner
from app.core.security import hash_password
from app.models.analisis import Analisis
from app.models.nota import Nota
from app.models.paciente import Paciente
from app.models.usuario import EstadoCuenta, RolUsuario, Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioOut, UsuarioUpdate

router = APIRouter(prefix="/owner", tags=["Owner"])

templates = Jinja2Templates(directory="app/templates")


def _con_cantidad_pacientes(db: Session, usuario: Usuario) -> UsuarioOut:
    cantidad = (
        db.query(func.count(Paciente.id))
        .filter(Paciente.usuario_id == usuario.id)
        .scalar()
    )
    return UsuarioOut(
        id=usuario.id,
        nombre=usuario.nombre,
        username=usuario.username,
        rol=usuario.rol,
        especialidad=usuario.especialidad,
        estado=usuario.estado,
        cantidad_pacientes=cantidad or 0,
    )


@router.get("", response_class=HTMLResponse)
def panel_owner(request: Request):
    """Panel de gestión de médicos. Protegido por las llamadas a
    /owner/usuarios (403 si el rol no es owner); ver JS de owner.html."""
    return templates.TemplateResponse(request=request, name="owner.html")


# ✅ crear usuario
@router.post("/usuarios", response_model=UsuarioOut)
def crear_usuario(
    usuario: UsuarioCreate,
    db: Session = Depends(get_db),
    owner = Depends(get_current_owner)
):

    existe = db.query(Usuario).filter(
        Usuario.username == usuario.username
    ).first()

    if existe:
        raise HTTPException(status_code=400, detail="Usuario ya existe")

    nuevo = Usuario(
        nombre=usuario.nombre,
        username=usuario.username,
        password=hash_password(usuario.password),
        rol=usuario.rol,
        especialidad=usuario.especialidad,
        # Si el owner lo da de alta a mano, ya esta aprobado por
        # definicion - no pasa por la cola de pendientes de /registro.
        estado=EstadoCuenta.ACTIVO,
    )

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return _con_cantidad_pacientes(db, nuevo)


# ✅ listar usuarios (con cantidad de pacientes por médico)
@router.get("/usuarios", response_model=list[UsuarioOut])
def listar_usuarios(
    db: Session = Depends(get_db),
    owner = Depends(get_current_owner)
):
    resultados = (
        db.query(Usuario, func.count(Paciente.id).label("cantidad_pacientes"))
        .outerjoin(Paciente, Paciente.usuario_id == Usuario.id)
        .group_by(Usuario.id)
        .order_by(Usuario.username)
        .all()
    )

    return [
        UsuarioOut(
            id=usuario.id,
            nombre=usuario.nombre,
            username=usuario.username,
            rol=usuario.rol,
            especialidad=usuario.especialidad,
            estado=usuario.estado,
            cantidad_pacientes=cantidad,
        )
        for usuario, cantidad in resultados
    ]


# ✅ activar/desactivar y reasignar especialidad
@router.put("/usuarios/{id}", response_model=UsuarioOut)
def actualizar_usuario(
    id: int,
    data: UsuarioUpdate,
    db: Session = Depends(get_db),
    owner = Depends(get_current_owner)
):
    usuario = db.query(Usuario).filter(Usuario.id == id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(usuario, key, value)

    db.commit()
    db.refresh(usuario)

    return _con_cantidad_pacientes(db, usuario)


@router.get("/estadisticas")
def obtener_estadisticas(
    db: Session = Depends(get_db),
    owner = Depends(get_current_owner)
):
    """Números agregados de toda la plataforma para el panel owner: solo
    COUNT/GROUP BY, nunca se traen filas completas ni se toca contenido
    clínico (datos_clinicos, notas.contenido, analisis_valores.valor) —
    el owner gestiona médicos, no ve historias clínicas."""

    medicos_total = (
        db.query(func.count(Usuario.id))
        .filter(Usuario.rol == RolUsuario.MEDICO)
        .scalar()
    )
    medicos_activos = (
        db.query(func.count(Usuario.id))
        .filter(Usuario.rol == RolUsuario.MEDICO, Usuario.estado == EstadoCuenta.ACTIVO)
        .scalar()
    )
    medicos_por_especialidad = dict(
        db.query(Usuario.especialidad, func.count(Usuario.id))
        .filter(Usuario.rol == RolUsuario.MEDICO)
        .group_by(Usuario.especialidad)
        .all()
    )

    pacientes_total = db.query(func.count(Paciente.id)).scalar()
    pacientes_por_especialidad = dict(
        db.query(Usuario.especialidad, func.count(Paciente.id))
        .select_from(Paciente)
        .join(Usuario, Paciente.usuario_id == Usuario.id)
        .group_by(Usuario.especialidad)
        .all()
    )

    notas_total = db.query(func.count(Nota.id)).scalar()

    analisis_total = db.query(func.count(Analisis.id)).scalar()
    analisis_por_especialidad = dict(
        db.query(Usuario.especialidad, func.count(Analisis.id))
        .select_from(Analisis)
        .join(Paciente, Analisis.paciente_id == Paciente.id)
        .join(Usuario, Paciente.usuario_id == Usuario.id)
        .group_by(Usuario.especialidad)
        .all()
    )

    return {
        "medicos": {
            "total": medicos_total,
            "activos": medicos_activos,
            "inactivos": medicos_total - medicos_activos,
            "por_especialidad": medicos_por_especialidad,
        },
        "pacientes": {
            "total": pacientes_total,
            "por_especialidad": pacientes_por_especialidad,
        },
        "notas": {"total": notas_total},
        "analisis": {
            "total": analisis_total,
            "por_especialidad": analisis_por_especialidad,
        },
    }
