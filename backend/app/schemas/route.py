from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.schemas.stop import StopInRoute


class RouteStopIn(BaseModel):
    stop_id: int
    order_index: int


class RouteBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    color: str = Field(default="#3B82F6", pattern=r"^#[0-9A-Fa-f]{6}$")


class RouteCreate(RouteBase):
    stops: Optional[List[RouteStopIn]] = []


class RouteUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    stops: Optional[List[RouteStopIn]] = None


class RouteOut(RouteBase):
    id: int
    created_at: datetime
    empresa: Optional[str] = None
    recorrido: Optional[str] = None
    calles: Optional[List[str]] = None
    fuente: Optional[str] = None

    model_config = {"from_attributes": True}


class RouteWithStops(RouteOut):
    stops: List["StopInRoute"] = []


# Necesario para resolver la referencia forward
from app.schemas.stop import StopInRoute  # noqa: E402, F401
RouteWithStops.model_rebuild()
