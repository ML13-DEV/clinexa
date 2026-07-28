from typing import Type, TypeVar

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.paciente import Paciente

ModeloConPaciente = TypeVar("ModeloConPaciente")


def get_paciente_propio(db: Session, paciente_id: int, usuario_id: int) -> Paciente:
    """Busca un paciente que pertenezca a usuario_id.

    Devuelve 404 (no 403) cuando el paciente existe pero es de otro médico,
    para no confirmarle a un atacante que el ID corresponde a un paciente real.
    Toda ruta que reciba paciente_id (pacientes, notas, analisis, turnos)
    debe pasar por acá antes de leer o modificar algo.
    """
    paciente = (
        db.query(Paciente)
        .filter(Paciente.id == paciente_id, Paciente.usuario_id == usuario_id)
        .first()
    )
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente


def get_registro_de_paciente_propio(
    db: Session,
    modelo: Type[ModeloConPaciente],
    registro_id: int,
    usuario_id: int,
    detail: str = "No encontrado",
) -> ModeloConPaciente:
    """Busca por id un registro que cuelga de un paciente (Nota, Analisis,
    Turno, ...) validando transitivamente que el paciente sea del usuario.

    `modelo` debe tener una columna `paciente_id` y `id`. Igual que
    get_paciente_propio, devuelve 404 en vez de 403 si el registro es de
    otro médico.
    """
    registro = (
        db.query(modelo)
        .join(Paciente, modelo.paciente_id == Paciente.id)
        .filter(modelo.id == registro_id, Paciente.usuario_id == usuario_id)
        .first()
    )
    if not registro:
        raise HTTPException(status_code=404, detail=detail)
    return registro
