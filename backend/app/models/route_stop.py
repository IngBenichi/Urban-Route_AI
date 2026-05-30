from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class RouteStop(Base):
    __tablename__ = "route_stops"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False, index=True)
    stop_id = Column(Integer, ForeignKey("stops.id", ondelete="CASCADE"), nullable=False, index=True)
    order_index = Column(Integer, nullable=False)

    __table_args__ = (UniqueConstraint("route_id", "stop_id", "order_index", name="uq_route_stop_order"),)

    route = relationship("Route", back_populates="route_stops")
    stop = relationship("Stop", back_populates="route_stops")
