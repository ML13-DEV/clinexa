from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_owner
from app.core.security import hash_password
from app.models.paciente import Paciente
from app.models.usuario import Usuario
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
        username=usuario.username,
        rol=usuario.rol,
        especialidad=usuario.especialidad,
        activo=usuario.activo,
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
        username=usuario.username,
        password=hash_password(usuario.password),
        rol=usuario.rol,
        especialidad=usuario.especialidad,
        activo=True
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
            username=usuario.username,
            rol=usuario.rol,
            especialidad=usuario.especialidad,
            activo=usuario.activo,
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
