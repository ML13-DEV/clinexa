from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database import SessionLocal
from app.models.usuario import EstadoCuenta, Usuario

security = HTTPBearer()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    """Devuelve el payload del JWT (sub, id, rol, especialidad).

    Además vuelve a consultar la cuenta contra la base en cada request
    (no solo al loguear): si el owner suspende/rechaza a alguien con una
    sesión ya abierta, el corte de acceso es inmediato, no recién cuando
    el JWT (24hs) expire. Necesario para la Fase B (pago vencido = pierde
    acceso ya, sin esperar)."""
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    # Los tokens de reset de contraseña (ver crear_token_reset) llevan un
    # "purpose" que un token de sesión normal nunca tiene: si alguien
    # intercepta un link de reset, no debe poder usarlo también como
    # sesión autenticada.
    if payload.get("purpose"):
        raise HTTPException(status_code=401, detail="Token inválido")

    usuario = db.query(Usuario).filter(Usuario.id == payload.get("id")).first()
    if not usuario or usuario.estado != EstadoCuenta.ACTIVO:
        raise HTTPException(status_code=403, detail="Tu cuenta no está activa")

    return payload


def get_current_owner(user: dict = Depends(get_current_user)) -> dict:
    if user.get("rol") != "owner":
        raise HTTPException(status_code=403, detail="No autorizado")
    return user


def get_current_medico(user: dict = Depends(get_current_user)) -> dict:
    """Para los endpoints clínicos (pacientes/notas/analisis/turnos): un
    owner tiene un JWT válido pero no gestiona pacientes, así que no debe
    poder pegarle a estas rutas."""
    if user.get("rol") != "medico":
        raise HTTPException(status_code=403, detail="No autorizado")
    return user
