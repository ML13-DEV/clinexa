from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_db
from app.core.limiter import limiter
from app.core.mail import enviar_mail_reset
from app.core.security import (
    crear_token,
    crear_token_reset,
    decode_token,
    hash_password,
    verificar_token_reset,
    verify_password,
)
from app.especialidades.config import CAMPOS_POR_ESPECIALIDAD
from app.models.usuario import EstadoCuenta, RolUsuario, Usuario
from app.schemas.usuario import ConfirmarReset, LoginSchema, RegistroCreate, SolicitudReset

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
        email=data.email,
        estado=EstadoCuenta.PENDIENTE,
    )
    db.add(nuevo)
    db.commit()

    return {"mensaje": "Registro recibido. Tu cuenta va a quedar pendiente de aprobación."}


@router.get("/olvide-password", response_class=HTMLResponse)
def olvide_password_page(request: Request):
    return templates.TemplateResponse(request, "olvide_password.html", {})


@router.post("/olvide-password")
def solicitar_reset(data: SolicitudReset, db: Session = Depends(get_db)):
    """Mismo mensaje exista o no la cuenta, y tenga o no email cargado:
    no hay que darle a quien pregunta ninguna señal de qué usuarios
    existen (user enumeration)."""
    usuario = db.query(Usuario).filter(
        (Usuario.username == data.identificador) | (Usuario.email == data.identificador)
    ).first()

    if usuario and usuario.email:
        token = crear_token_reset(usuario.id, usuario.password)
        link = f"{settings.app_base_url}/reset-password?token={token}"
        enviar_mail_reset(usuario.email, usuario.nombre, link)

    return {"mensaje": "Si el usuario existe y tiene un email cargado, te enviamos un mail con instrucciones."}


@router.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(request: Request):
    return templates.TemplateResponse(request, "resetear_password.html", {})


@router.post("/reset-password")
def confirmar_reset(data: ConfirmarReset, db: Session = Depends(get_db)):
    try:
        payload = decode_token(data.token)
    except JWTError:
        raise HTTPException(status_code=400, detail="Link inválido o vencido")

    usuario = db.query(Usuario).filter(Usuario.id == payload.get("id")).first()
    if not usuario or not verificar_token_reset(data.token, usuario.id, usuario.password):
        raise HTTPException(status_code=400, detail="Link inválido o vencido")

    usuario.password = hash_password(data.password_nueva)
    db.commit()

    return {"mensaje": "Contraseña actualizada. Ya podés iniciar sesión."}
