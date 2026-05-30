import math
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.search import SearchRequest, SearchResponse, PlanRequest, RoutePlan, RouteStep
from app.services.search_engine import search_routes
from app.services.nominatim import geocode
from app.services.ai_engine import get_ai_recommendation

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search(body: SearchRequest, db: AsyncSession = Depends(get_db)):
    return await search_routes(
        db=db,
        origin=body.origin,
        destination=body.destination,
        search_type=body.search_type,
        origin_lat=body.origin_lat,
        origin_lon=body.origin_lon,
        dest_lat=body.dest_lat,
        dest_lon=body.dest_lon,
    )


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    """Distancia en metros entre dos puntos GPS."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return int(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


@router.post("/plan", response_model=RoutePlan)
async def plan_route(body: PlanRequest, db: AsyncSession = Depends(get_db)):
    """
    Planifica una ruta completa:
    1. Geocodifica el destino
    2. Busca rutas desde coords del usuario
    3. Devuelve pasos: caminar → bus → caminar + narración IA
    """
    # 1. Geocodificar destino
    dest = await geocode(body.destination)
    if not dest:
        raise HTTPException(status_code=404, detail=f"No se encontró '{body.destination}' en el mapa.")

    # 2. Buscar rutas usando coordenadas
    results = await search_routes(
        db=db,
        origin="Mi ubicación",
        destination=body.destination,
        search_type="coords",
        origin_lat=body.origin_lat,
        origin_lon=body.origin_lon,
        dest_lat=dest["lat"],
        dest_lon=dest["lon"],
    )

    if not results.direct and not results.transfers:
        return RoutePlan(
            found=False,
            destination_name=dest["display_name"],
            dest_lat=dest["lat"],
            dest_lon=dest["lon"],
        )

    steps: list[RouteStep] = []
    total_time = 0

    # Elegir la MEJOR opción comparando tiempo total de la mejor directa vs. mejor transbordo.
    # `time_min` ya incluye caminatas porque el motor las cuenta en el score.
    best_direct   = results.direct[0]   if results.direct   else None
    best_transfer = results.transfers[0] if results.transfers else None

    use_transfer = (
        best_transfer is not None
        and (best_direct is None or best_transfer.time_min < best_direct.time_min)
    )

    if not use_transfer and best_direct:
        best = best_direct

        walk_m = _haversine_m(body.origin_lat, body.origin_lon, best.from_stop.lat, best.from_stop.lon)
        walk_min = max(1, round(walk_m / 83))   # ~83 m/min ≈ 5 km/h
        steps.append(RouteStep(
            type="walk",
            instruction=f"Camina {walk_m}m hasta el paradero '{best.from_stop.name}'",
            distance_m=walk_m,
            stop_name=best.from_stop.name,
            stop_lat=best.from_stop.lat,
            stop_lon=best.from_stop.lon,
        ))
        steps.append(RouteStep(
            type="bus",
            instruction=f"Toma el bus {best.route.name} desde '{best.from_stop.name}' hasta '{best.to_stop.name}'",
            route_name=best.route.name,
            route_color=best.route.color,
            stop_name=best.from_stop.name,
            stop_lat=best.from_stop.lat,
            stop_lon=best.from_stop.lon,
        ))
        walk2_m   = _haversine_m(best.to_stop.lat, best.to_stop.lon, dest["lat"], dest["lon"])
        walk2_min = max(1, round(walk2_m / 83))
        steps.append(RouteStep(
            type="walk",
            instruction=f"Bájate en '{best.to_stop.name}' y camina {walk2_m}m hasta '{body.destination}'",
            distance_m=walk2_m,
            stop_name=best.to_stop.name,
            stop_lat=best.to_stop.lat,
            stop_lon=best.to_stop.lon,
        ))
        total_time = walk_min + best.time_min + walk2_min

    else:
        best = best_transfer

        walk_m    = _haversine_m(body.origin_lat, body.origin_lon, best.from_stop.lat, best.from_stop.lon)
        walk_min  = max(1, round(walk_m / 83))
        steps.append(RouteStep(
            type="walk",
            instruction=f"Camina {walk_m}m hasta el paradero '{best.from_stop.name}'",
            distance_m=walk_m,
            stop_name=best.from_stop.name,
            stop_lat=best.from_stop.lat,
            stop_lon=best.from_stop.lon,
        ))
        steps.append(RouteStep(
            type="bus",
            instruction=f"Toma el bus {best.route_a.name} hasta '{best.transfer_stop.name}' (transbordo)",
            route_name=best.route_a.name,
            route_color=best.route_a.color,
            stop_name=best.from_stop.name,
            stop_lat=best.from_stop.lat,
            stop_lon=best.from_stop.lon,
        ))

        # Si el transbordo requiere caminar entre dos paradas distintas
        transfer_stop_board = best.transfer_stop_b or best.transfer_stop
        if best.transfer_walk_m and best.transfer_walk_m > 30:
            steps.append(RouteStep(
                type="walk",
                instruction=f"Camina {best.transfer_walk_m}m hasta el paradero '{transfer_stop_board.name}' para tomar el siguiente bus",
                distance_m=best.transfer_walk_m,
                stop_name=transfer_stop_board.name,
                stop_lat=transfer_stop_board.lat,
                stop_lon=transfer_stop_board.lon,
            ))

        steps.append(RouteStep(
            type="bus",
            instruction=f"Transborda al bus {best.route_b.name} desde '{transfer_stop_board.name}' hasta '{best.to_stop.name}'",
            route_name=best.route_b.name,
            route_color=best.route_b.color,
            stop_name=transfer_stop_board.name,
            stop_lat=transfer_stop_board.lat,
            stop_lon=transfer_stop_board.lon,
        ))
        walk2_m   = _haversine_m(best.to_stop.lat, best.to_stop.lon, dest["lat"], dest["lon"])
        walk2_min = max(1, round(walk2_m / 83))
        steps.append(RouteStep(
            type="walk",
            instruction=f"Bájate en '{best.to_stop.name}' y camina {walk2_m}m hasta '{body.destination}'",
            distance_m=walk2_m,
            stop_name=best.to_stop.name,
            stop_lat=best.to_stop.lat,
            stop_lon=best.to_stop.lon,
        ))
        total_time = walk_min + best.time_min + walk2_min

    # 3. Narración IA
    steps_text = "\n".join(f"- {s.instruction}" for s in steps)
    ai_query = (
        f"El usuario quiere ir a '{body.destination}'. "
        f"La ruta planificada tiene estos pasos:\n{steps_text}\n"
        f"Tiempo total estimado: {total_time} minutos. "
        f"Explica la ruta de forma amigable y da consejos útiles."
    )
    narration = await get_ai_recommendation(ai_query)

    return RoutePlan(
        found=True,
        destination_name=dest["display_name"],
        dest_lat=dest["lat"],
        dest_lon=dest["lon"],
        steps=steps,
        total_time_min=total_time,
        ai_narration=narration,
    )
