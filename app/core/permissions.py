from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.paciente import Paciente


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
