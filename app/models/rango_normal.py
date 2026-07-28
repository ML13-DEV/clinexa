from sqlalchemy import Column, Integer, Float, String, UniqueConstraint
from app.database import Base


class RangoNormal(Base):
    """Rango normal de un análisis por especialidad, para colorear
    resultados (rojo/alto, azul/bajo, verde/normal) en el frontend.

    Estructura preparada, todavía sin endpoints ni lógica de coloreado:
    ver .valor-alto/.valor-bajo/.valor-normal en styles.css y
    colorearValor() en paciente.html, que ya esperan esto pero no lo
    consultan aún.
    """

    __tablename__ = "rangos_normales"
    __table_args__ = (
        UniqueConstraint("especialidad", "analisis_key", name="uq_rango_especialidad_key"),
    )

    id = Column(Integer, primary_key=True, index=True)
    especialidad = Column(String(50), nullable=False, index=True)
    analisis_key = Column(String(50), nullable=False)
    valor_min = Column(Float, nullable=True)
    valor_max = Column(Float, nullable=True)
