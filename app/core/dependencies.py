from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database import SessionLocal

security = HTTPBearer()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Devuelve el payload del JWT (sub, id, rol, especialidad)."""
    try:
        return decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")


def get_current_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("rol") != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")
    return user
