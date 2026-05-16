from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioOut
from app.auth import hash_password, get_current_user

router = APIRouter(prefix="/admin", tags=["Admin"])


# 🔒 verificar admin
def require_admin(user=Depends(get_current_user)):
    
    if user["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")

    return user


# ✅ crear usuario
@router.post("/usuarios", response_model=UsuarioOut)
def crear_usuario(
    usuario: UsuarioCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
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

    return nuevo


# ✅ listar usuarios
@router.get("/usuarios", response_model=list[UsuarioOut])
def listar_usuarios(
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):

    return db.query(Usuario).all()