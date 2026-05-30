from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship

from app.database import Base


class Stop(Base):
    __tablename__ = "stops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    code = Column(String(50), nullable=True)

    route_stops = relationship("RouteStop", back_populates="stop")
