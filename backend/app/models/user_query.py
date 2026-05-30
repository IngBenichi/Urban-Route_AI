from sqlalchemy import Column, Integer, Text, DateTime, func

from app.database import Base


class UserQuery(Base):
    __tablename__ = "user_queries"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
