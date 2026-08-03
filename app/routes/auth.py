from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_db
from app.core.limiter import limiter
from app.core.security import verify_password, hash_password, crear_token
from app.especialidades.config import CAMPOS_POR_ESPECIALIDAD
from app.models.usuario import EstadoCuenta, RolUsuario, Usuario
from app.schemas.usuario import LoginSchema, RegistroCreate

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

MENSAJE_POR_ESTADO = {
    EstadoCuenta.PENDIENTE: "Tu cuenta está pendiente de aprobación.",
    EstadoCuenta.RECHAZADO: "Tu solicitud de registro fue rechazada. Contactá al administrador.",
    EstadoCuenta.SUSPENDIDO: "Tu cuenta está desactivada. Contactá al administrador.",
}


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {})

@router.post("/login")
@limiter.limit(settings.login_rate_limit)
def login(request: Request, user: LoginSchema, db: Session = Depends(get_db)):

    usuario = db.query(Usuario).filter_by(username=user.username).first()

    if not usuario or not verify_password(user.password, usuario.password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    if usuario.estado != EstadoCuenta.ACTIVO:
        mensaje = MENSAJE_POR_ESTADO.get(usuario.estado, "Tu cuenta no está activa.")
        raise HTTPException(status_code=403, detail=mensaje)

    token = crear_token({
        "sub": usuario.username,
        "rol": usuario.rol,
        "especialidad": usuario.especialidad,
        "id": usuario.id
    })

    return {"access_token": token, "rol": usuario.rol}


@router.get("/registro", response_class=HTMLResponse)
def registro_page(request: Request):
    return templates.TemplateResponse(request, "registro.html", {})


@router.post("/registro", status_code=201)
def registro(data: RegistroCreate, db: Session = Depends(get_db)):
    """Alta pública: rol se fuerza a medico y la cuenta queda pendiente
    de aprobación del owner (ver EstadoCuenta). No devuelve token: hasta
    que no lo aprueben, no puede loguearse."""

    if data.especialidad not in CAMPOS_POR_ESPECIALIDAD:
        raise HTTPException(status_code=422, detail="Especialidad no válida")

    existe = db.query(Usuario).filter(Usuario.username == data.username).first()
    if existe:
        raise HTTPException(status_code=400, detail="Ese usuario ya existe")

    nuevo = Usuario(
        nombre=data.nombre,
        username=data.username,
        password=hash_password(data.password),
        rol=RolUsuario.MEDICO,
        especialidad=data.especialidad,
        estado=EstadoCuenta.PENDIENTE,
    )
    db.add(nuevo)
    db.commit()

    return {"mensaje": "Registro recibido. Tu cuenta va a quedar pendiente de aprobación."}
