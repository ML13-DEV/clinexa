from sqlalchemy import Column, Integer, String, Date, Text, Float, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base
from sqlalchemy.orm import relationship

class Paciente(Base):
    __tablename__ = "pacientes"
    __table_args__ = (
        # El mismo DNI puede repetirse entre pacientes de médicos distintos
        # (son historias clínicas independientes); lo que no puede repetirse
        # es el DNI dos veces para el mismo médico.
        UniqueConstraint("usuario_id", "dni", name="uq_paciente_usuario_dni"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Dueño del registro: el médico que lo creó. Todas las queries de
    # pacientes/notas/turnos/analisis deben filtrar por esta columna
    # (directa o transitivamente vía paciente_id) para que un médico
    # nunca vea pacientes de otro.
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)

    # Datos personales
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    dni = Column(String(20), index=True)
    fecha_nacimiento = Column(Date)
    telefono = Column(String(30))

    # Obra social
    obra_social = Column(String(100))
    numero_afiliado = Column(String(100))

    # Datos médicos comunes a cualquier especialidad
    alergias = Column(Text)
    medico_cabecera = Column(String(100))

    # Campos específicos de la especialidad del médico dueño (ver
    # app/especialidades/config.py para qué keys son válidas por
    # especialidad). Ej. hematología: sangrados, trombosis, gestas,
    # vacunas, fim_descriptivo.
    datos_clinicos = Column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=False,
        default=dict,
        server_default="{}",
    )

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