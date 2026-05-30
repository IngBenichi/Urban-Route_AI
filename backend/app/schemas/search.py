from typing import Optional, List, Literal

from pydantic import BaseModel, Field

from app.schemas.stop import StopOut
from app.schemas.route import RouteOut


class SearchRequest(BaseModel):
    origin: str = Field(..., min_length=1, max_length=255, description="Nombre del paradero o lugar de origen")
    destination: str = Field(..., min_length=1, max_length=255, description="Nombre del paradero o lugar de destino")
    search_type: Literal["text", "coords"] = "text"
    origin_lat: Optional[float] = Field(None, ge=-90, le=90)
    origin_lon: Optional[float] = Field(None, ge=-180, le=180)
    dest_lat: Optional[float] = Field(None, ge=-90, le=90)
    dest_lon: Optional[float] = Field(None, ge=-180, le=180)


class PlanRequest(BaseModel):
    destination: str = Field(..., min_length=1, max_length=255)
    origin_lat: float = Field(..., ge=-90, le=90)
    origin_lon: float = Field(..., ge=-180, le=180)


class RouteStep(BaseModel):
    type: Literal["walk", "bus"]
    instruction: str          # "Camina 250m hasta Calle 72 con Carrera 46"
    distance_m: Optional[int] = None
    stop_name: Optional[str] = None
    stop_lat: Optional[float] = None
    stop_lon: Optional[float] = None
    route_name: Optional[str] = None
    route_color: Optional[str] = None


class RoutePlan(BaseModel):
    found: bool
    destination_name: str
    dest_lat: Optional[float] = None
    dest_lon: Optional[float] = None
    steps: List[RouteStep] = []
    total_time_min: int = 0
    ai_narration: Optional[str] = None


class DirectRouteResult(BaseModel):
    route: RouteOut
    from_stop: StopOut
    to_stop: StopOut
    stops_sequence: List[StopOut]
    distance_km: float
    time_min: int
    walk1_km: float = 0.0   # caminata desde origen al paradero de subida
    walk2_km: float = 0.0   # caminata desde paradero de bajada al destino


class TransferRouteResult(BaseModel):
    route_a: RouteOut
    route_b: RouteOut
    from_stop: StopOut
    transfer_stop: StopOut      # parada de bajada del bus A
    transfer_stop_b: Optional[StopOut] = None  # parada de subida al bus B (puede ser distinta)
    to_stop: StopOut
    distance_km: float
    time_min: int
    walk1_km: float = 0.0
    walk2_km: float = 0.0
    transfer_walk_m: int = 0    # metros entre transfer_stop y transfer_stop_b


class SearchResponse(BaseModel):
    origin_query: str
    destination_query: str
    direct: List[DirectRouteResult]
    transfers: List[TransferRouteResult]
    total_results: int
