from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.nota import Nota
from app.schemas.nota import NotaCreate
from app.auth import get_current_user

router = APIRouter(
    dependencies=[Depends(get_current_user)]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/notas")
def crear_nota(
    nota: NotaCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
    ):
    
    nueva_nota = Nota(**nota.dict())
    db.add(nueva_nota)
    db.commit()
    db.refresh(nueva_nota)
    return nueva_nota