import hashlib
from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

RESET_TOKEN_PURPOSE = "password_reset"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def crear_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict:
    """Puede levantar jose.JWTError si el token es inválido o expiró."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


def _fingerprint(password_hash: str) -> str:
    return hashlib.sha256(password_hash.encode()).hexdigest()[:16]


def crear_token_reset(usuario_id: int, password_hash: str) -> str:
    """Token de un solo uso "de facto" sin tabla propia: lleva un
    fingerprint del hash de contraseña vigente al momento de emitirlo.
    Apenas la contraseña cambia (reset exitoso), el fingerprint deja de
    matchear y el token queda inválido aunque no haya expirado todavía -
    mismo truco que usa Django para esto. `purpose` lo distingue de un
    token de sesión normal (ver get_current_user, que rechaza cualquier
    token que lo tenga: este token nunca debe servir para autenticarse)."""
    expire = datetime.utcnow() + timedelta(minutes=settings.reset_password_token_expire_minutes)
    payload = {
        "id": usuario_id,
        "purpose": RESET_TOKEN_PURPOSE,
        "fp": _fingerprint(password_hash),
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def verificar_token_reset(token: str, usuario_id: int, password_hash: str) -> bool:
    try:
        payload = decode_token(token)
    except JWTError:
        return False

    return (
        payload.get("purpose") == RESET_TOKEN_PURPOSE
        and payload.get("id") == usuario_id
        and payload.get("fp") == _fingerprint(password_hash)
    )
