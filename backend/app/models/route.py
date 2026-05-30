from sqlalchemy import Column, Integer, String, DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True)
    color = Column(String(7), nullable=False, default="#3B82F6")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Campos enriquecidos provenientes de las resoluciones AMBQ
    empresa = Column(String(100), nullable=True)
    recorrido = Column(Text, nullable=True)
    calles = Column(JSONB, nullable=True)   # lista ordenada de vías del recorrido
    fuente = Column(String(50), nullable=True)  # ej. "ambq_resolucion"

    route_stops = relationship(
        "RouteStop",
        back_populates="route",
        order_by="RouteStop.order_index",
        cascade="all, delete-orphan",
    )
