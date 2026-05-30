from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class StopBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    code: Optional[str] = Field(None, max_length=50)


class StopCreate(StopBase):
    pass


class StopUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    code: Optional[str] = Field(None, max_length=50)


class StopOut(StopBase):
    id: int

    model_config = {"from_attributes": True}


class StopInRoute(BaseModel):
    """Stop with its position within a route."""
    id: int
    name: str
    lat: Optional[float]
    lon: Optional[float]
    code: Optional[str]
    order_index: int

    model_config = {"from_attributes": True}
