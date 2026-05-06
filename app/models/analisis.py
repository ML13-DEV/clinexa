from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Analisis(Base):
    __tablename__ = "analisis"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"))

    fecha = Column(DateTime, default=datetime.utcnow)

    # 🧪 HEMOGRAMA
    gb = Column(Float, nullable=True)
    nt = Column(Float, nullable=True)
    l = Column(Float, nullable=True)
    hb = Column(Float, nullable=True)
    htd = Column(Float, nullable=True)
    vcm = Column(Float, nullable=True)
    pqts = Column(Float, nullable=True)

    # 🧪 HIERRO
    ferremia = Column(Float, nullable=True)
    ferritina = Column(Float, nullable=True)
    saturacion = Column(Float, nullable=True)
    tibc = Column(Float, nullable=True)

    # 🧪 OTROS
    epo = Column(Float, nullable=True)
    vit_b12 = Column(Float, nullable=True)
    af = Column(Float, nullable=True)

    # 🧪 FUNCIONES
    hepatograma = Column(String, nullable=True)
    funcion_renal = Column(String, nullable=True)

    # 🧪 COAGULACIÓN
    tp = Column(Float, nullable=True)
    kptt = Column(Float, nullable=True)
    rino = Column(Float, nullable=True)

    paciente = relationship("Paciente")