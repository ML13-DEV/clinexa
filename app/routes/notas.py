from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.nota import Nota
from app.schemas.nota import NotaCreate, NotaUpdate
from app.core.permissions import get_paciente_propio, get_registro_de_paciente_propio
from app.core.dependencies import get_db, get_current_user, get_current_medico

router = APIRouter(
    dependencies=[Depends(get_current_medico)]
)


@router.post("/notas")
def crear_nota(
    nota: NotaCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
    ):

    # Valida que el paciente exista y sea del médico logueado antes de
    # dejarle colgar una nota de cualquier paciente_id.
    get_paciente_propio(db, nota.paciente_id, user["id"])

    nueva_nota = Nota(**nota.dict())
    db.add(nueva_nota)
    db.commit()
    db.refresh(nueva_nota)
    return nueva_nota


@router.put("/notas/{id}")
def actualizar_nota(
    id: int,
    data: NotaUpdate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
    ):

    nota = get_registro_de_paciente_propio(db, Nota, id, user["id"], detail="Nota no encontrada")

    cambios = data.dict(exclude_unset=True)

    for key, value in cambios.items():
        setattr(nota, key, value)

    db.commit()
    db.refresh(nota)

    return nota


@router.delete("/notas/{id}")
def eliminar_nota(
    id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
    ):

    nota = get_registro_de_paciente_propio(db, Nota, id, user["id"], detail="Nota no encontrada")

    db.delete(nota)
    db.commit()

    return {"ok": True}