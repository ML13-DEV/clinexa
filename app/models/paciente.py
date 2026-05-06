from sqlalchemy import Column, Integer, String, Date, Text
from app.database import Base
from sqlalchemy.orm import relationship

class Paciente(Base):
    __tablename__ = "pacientes"

    id = Column(Integer, primary_key=True, index=True)

    # Datos personales
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    dni = Column(String, unique=True, index=True)
    fecha_nacimiento = Column(Date)
    telefono = Column(String)

    # Obra social
    obra_social = Column(String)
    numero_afiliado = Column(String)

    # Datos médicos
    sangrados = Column(Text)
    trombosis = Column(Text)
    alergias = Column(Text)
    vacunas = Column(Text)
    gestas = Column(Text)
    medico_cabecera = Column(String)
    fim_descriptivo = Column(Text)

    # Relaciones
    turnos = relationship("Turno", back_populates="paciente")
    notas = relationship("Nota", back_populates="paciente")