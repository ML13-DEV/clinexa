from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Analisis(Base):
    """Header de un evento de laboratorio (una fecha, un paciente). Los
    valores de cada determinación (gb, hb, hto, ...) cuelgan de acá en
    AnalisisValor, normalizados en vez de columnas fijas: así cualquier
    especialidad puede tener su propio panel de análisis sin migrar el
    esquema, y a futuro rangos_normales se cruza con un JOIN de SQL
    directo por (especialidad, analisis_key)."""

    __tablename__ = "analisis"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False, index=True)
    fecha = Column(DateTime, default=datetime.utcnow)

    paciente = relationship("Paciente")
    valores = relationship(
        "AnalisisValor", back_populates="analisis", cascade="all, delete-orphan"
    )


class AnalisisValor(Base):
    __tablename__ = "analisis_valores"
    __table_args__ = (
        UniqueConstraint("analisis_id", "analisis_key", name="uq_analisis_valor_key"),
    )

    id = Column(Integer, primary_key=True, index=True)
    analisis_id = Column(
        Integer, ForeignKey("analisis.id", ondelete="CASCADE"), nullable=False, index=True
    )
    analisis_key = Column(String(50), nullable=False, index=True)

    # Texto libre: cubre tanto valores numéricos (guardados como string,
    # ej. "13.2") como texto (hepatograma, funcion_renal, otros_analisis).
    # Cuando exista rangos_normales, castear a float lo que se pueda y
    # dejar sin colorear lo que no.
    valor = Column(String(255))

    analisis = relationship("Analisis", back_populates="valores")
