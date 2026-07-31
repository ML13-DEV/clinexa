from sqlalchemy import Column, Integer, String, Date, Text, Float
from app.database import Base
from sqlalchemy.orm import relationship

class Paciente(Base):
    __tablename__ = "pacientes"

    id = Column(Integer, primary_key=True, index=True)

    # Datos personales
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    dni = Column(String(20), unique=True, index=True)
    fecha_nacimiento = Column(Date)
    telefono = Column(String(30))
    localidad = Column(String(150))

    # Obra social
    obra_social = Column(String(100))
    numero_afiliado = Column(String(100))

    # Datos médicos
    sangrados = Column(Text)
    trombosis = Column(Text)
    alergias = Column(Text)
    vacunas = Column(Text)
    gestas = Column(Text)
    medico_cabecera = Column(String(100))
    fim_descriptivo = Column(Text)

    # Datos clínicos (antropometría, historia clínica)
    peso = Column(Float)
    talla = Column(Float)
    imc = Column(Float)
    diagnostico_principal = Column(Text)
    ocupacion = Column(String(150))
    habitos = Column(Text)
    medicacion_habitual = Column(Text)
    cirugias = Column(Text)
    transfusiones = Column(Text)
    antecedentes_personales = Column(Text)
    antecedentes_familiares = Column(Text)

    # Relaciones
    turnos = relationship("Turno", back_populates="paciente")
    notas = relationship("Nota", back_populates="paciente")