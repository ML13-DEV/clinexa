from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import LoginSchema
from app.auth import verify_password, crear_token

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {})

@router.post("/login")
def login(user: LoginSchema, db: Session = Depends(get_db)):

    usuario = db.query(Usuario).filter_by(username=user.username).first()

    if not usuario or not verify_password(user.password, usuario.password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    token = crear_token({
        "sub": usuario.username,
        "rol": usuario.rol,
        "especialidad": usuario.especialidad,
        "id": usuario.id
    })

    return {"access_token": token}