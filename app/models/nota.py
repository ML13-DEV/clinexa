from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from app.database import Base
from datetime import datetime
from sqlalchemy.orm import relationship


class Nota(Base):
    __tablename__ = "notas"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"))
    contenido = Column(Text)
    
    # Mantenemos el default por seguridad, pero al venir en el "NotaCreate" 
    # SQLAlchemy usará el valor que tú le pases.
    fecha = Column(DateTime, default=datetime.utcnow) 
    
    paciente = relationship("Paciente", back_populates="notas")