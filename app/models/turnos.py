from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base
from datetime import datetime
from sqlalchemy.orm import relationship


class Turno(Base):
    __tablename__ = "turnos"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"))
    
    nombre_temp = Column(String, nullable=True)
    
    fecha = Column(DateTime, default=datetime.utcnow)
    motivo = Column(String)
    diagnostico = Column(String)
    observaciones = Column(String)
    
    estado = Column(String, default="pendiente")
    
    paciente = relationship("Paciente", back_populates="turnos")
    paciente_id = Column(Integer, ForeignKey("pacientes.id"))