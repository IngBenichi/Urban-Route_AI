from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.route import Route
from app.models.stop import Stop
from app.models.route_stop import RouteStop
from app.schemas.search import DirectRouteResult, TransferRouteResult, SearchResponse
from app.services.geo_engine import haversine, route_distance_km, estimated_time_min, stops_within_radius
from app.config import settings

# ── Constantes de velocidad ───────────────────────────────────────────────────
WALK_KMH = 5.0          # velocidad peatonal (~83 m/min)
TRANSFER_RADIUS_KM = 0.4  # radio para transbordo en paradas cercanas (400 m)


def _total_time_min(
    walk1_km: float,
    bus_km: float,
    walk2_km: float,
    transfer_walk_km: float = 0.0,
    bus_speed_kmh: float = 20.0,
) -> int:
    """Tiempo total del viaje en minutos, incluyendo todas las caminatas."""
    walk_min = (walk1_km + walk2_km + transfer_walk_km) / WALK_KMH * 60
    bus_min = bus_km / bus_speed_kmh * 60
    return max(1, round(walk_min + bus_min))


async def _find_stops_by_query(db: AsyncSession, query: str) -> List[Stop]:
    """Busca paraderos cuyo nombre contenga el texto dado (ILIKE)."""
    result = await db.execute(
        select(Stop).where(Stop.name.ilike(f"%{query}%")).limit(20)
    )
    return result.scalars().all()


# Paradas que NO son abordables (Barranquilla prohíbe tránsito de buses por su Av. Murillo)
_NON_BOARDABLE_STOP_IDS = {17}  # AVENIDA MURILLO* de Barranquilla


async def _find_stops_by_coords(
    db: AsyncSession, lat: float, lon: float, radius_km: float = 2.0
) -> List[Stop]:
    """Retorna los paraderos más cercanos a unas coordenadas dentro de un radio."""
    result = await db.execute(
        select(Stop).where(Stop.lat.isnot(None), Stop.id.not_in(_NON_BOARDABLE_STOP_IDS))
    )
    all_stops = result.scalars().all()
    return stops_within_radius(lat, lon, all_stops, radius_km)


async def _get_all_routes_with_stops(db: AsyncSession) -> List[Route]:
    """Carga todas las rutas con sus paraderos ordenados."""
    result = await db.execute(
        select(Route).options(
            selectinload(Route.route_stops).selectinload(RouteStop.stop)
        )
    )
    return result.scalars().all()


def _build_stop_sequence(route: Route, from_idx: int, to_idx: int) -> List[Stop]:
    """Extrae la secuencia de paraderos entre dos índices de una ruta."""
    ordered = sorted(route.route_stops, key=lambda rs: rs.order_index)
    return [rs.stop for rs in ordered if from_idx <= rs.order_index <= to_idx]


async def search_routes(
    db: AsyncSession,
    origin: str,
    destination: str,
    search_type: str = "text",
    origin_lat: Optional[float] = None,
    origin_lon: Optional[float] = None,
    dest_lat: Optional[float] = None,
    dest_lon: Optional[float] = None,
) -> SearchResponse:

    # 1. Encontrar paraderos de origen y destino
    if search_type == "coords" and origin_lat and origin_lon and dest_lat and dest_lon:
        origin_stops = await _find_stops_by_coords(db, origin_lat, origin_lon)
        dest_stops   = await _find_stops_by_coords(db, dest_lat, dest_lon)
    else:
        origin_stops = await _find_stops_by_query(db, origin)
        dest_stops   = await _find_stops_by_query(db, destination)

    if not origin_stops or not dest_stops:
        return SearchResponse(
            origin_query=origin,
            destination_query=destination,
            direct=[],
            transfers=[],
            total_results=0,
        )

    origin_ids = {s.id for s in origin_stops}
    dest_ids   = {s.id for s in dest_stops}

    # 2. Cargar todas las rutas con sus paraderos
    all_routes = await _get_all_routes_with_stops(db)

    # Índice: route_id → {stop_id → order_index}
    # Si una parada aparece varias veces en la ruta, guardamos el MÍNIMO índice
    # (primera vez que el bus llega a ella), para no inflar la distancia del segmento.
    route_stop_index: dict[int, dict[int, int]] = {}
    # Índice: route_id → {stop_id → Stop object}
    route_stop_obj: dict[int, dict[int, Stop]] = {}
    for route in all_routes:
        idx_map: dict[int, int] = {}
        obj_map: dict[int, Stop] = {}
        for rs in sorted(route.route_stops, key=lambda x: x.order_index):
            if rs.stop_id not in idx_map:
                idx_map[rs.stop_id] = rs.order_index
                obj_map[rs.stop_id] = rs.stop
        route_stop_index[route.id] = idx_map
        route_stop_obj[route.id]   = obj_map

    # Helper: distancia en km desde el origen del usuario a un paradero
    def _walk1(stop: Stop) -> float:
        if origin_lat and origin_lon and stop.lat and stop.lon:
            return haversine(origin_lat, origin_lon, stop.lat, stop.lon)
        return 0.0

    # Helper: distancia en km desde un paradero al destino final
    def _walk2(stop: Stop) -> float:
        if dest_lat and dest_lon and stop.lat and stop.lon:
            return haversine(stop.lat, stop.lon, dest_lat, dest_lon)
        return 0.0

    # 3. Rutas directas ────────────────────────────────────────────────────────
    direct_results: List[DirectRouteResult] = []
    for route in all_routes:
        stop_idx = route_stop_index[route.id]
        found_origins = [(sid, stop_idx[sid]) for sid in origin_ids if sid in stop_idx]
        found_dests   = [(sid, stop_idx[sid]) for sid in dest_ids   if sid in stop_idx]

        for o_sid, o_idx in found_origins:
            for d_sid, d_idx in found_dests:
                if o_idx >= d_idx:
                    continue  # destino debe ir después del origen en la secuencia
                origin_stop = route_stop_obj[route.id][o_sid]
                dest_stop   = route_stop_obj[route.id][d_sid]
                seq  = _build_stop_sequence(route, o_idx, d_idx)
                bus_km  = route_distance_km(seq)
                w1 = _walk1(origin_stop)
                w2 = _walk2(dest_stop)
                total_t = _total_time_min(w1, bus_km, w2, bus_speed_kmh=settings.BUS_AVG_SPEED_KMH)
                direct_results.append(DirectRouteResult(
                    route=route,
                    from_stop=origin_stop,
                    to_stop=dest_stop,
                    stops_sequence=seq,
                    distance_km=round(bus_km, 2),
                    time_min=total_t,
                    walk1_km=round(w1, 3),
                    walk2_km=round(w2, 3),
                ))

    # 4. Rutas con transbordo ──────────────────────────────────────────────────
    # Siempre se buscan (no solo cuando no hay directas) para poder comparar.
    transfer_results: List[TransferRouteResult] = []

    routes_with_origin = [
        r for r in all_routes
        if any(sid in route_stop_index[r.id] for sid in origin_ids)
    ]
    routes_with_dest = [
        r for r in all_routes
        if any(sid in route_stop_index[r.id] for sid in dest_ids)
    ]

    for route_a in routes_with_origin:
        idx_a  = route_stop_index[route_a.id]
        obj_a  = route_stop_obj[route_a.id]
        stops_a_sorted = sorted(route_a.route_stops, key=lambda rs: rs.order_index)

        # Paraderos del origen en la ruta A
        found_origins_a = [(sid, idx_a[sid]) for sid in origin_ids if sid in idx_a]
        if not found_origins_a:
            continue

        for route_b in routes_with_dest:
            if route_a.id == route_b.id:
                continue
            idx_b  = route_stop_index[route_b.id]
            obj_b  = route_stop_obj[route_b.id]
            stops_b_sorted = sorted(route_b.route_stops, key=lambda rs: rs.order_index)

            found_dests_b = [(sid, idx_b[sid]) for sid in dest_ids if sid in idx_b]
            if not found_dests_b:
                continue

            for o_sid, o_idx in found_origins_a:
                origin_stop = obj_a[o_sid]

                # Buscar paradas de transbordo: cualquier parada de A (después del origen)
                # que esté a ≤ TRANSFER_RADIUS_KM de alguna parada de B (antes del destino).
                for rs_a in stops_a_sorted:
                    if rs_a.order_index <= o_idx:
                        continue  # transbordo debe ser DESPUÉS del origen
                    ta_stop = rs_a.stop
                    if not ta_stop.lat or not ta_stop.lon:
                        continue

                    for rs_b in stops_b_sorted:
                        tb_stop = rs_b.stop
                        if not tb_stop.lat or not tb_stop.lon:
                            continue

                        transfer_walk_km = haversine(
                            ta_stop.lat, ta_stop.lon,
                            tb_stop.lat, tb_stop.lon
                        )
                        if transfer_walk_km > TRANSFER_RADIUS_KM:
                            continue

                        t_idx_b = rs_b.order_index
                        for d_sid, d_idx in found_dests_b:
                            if d_idx <= t_idx_b:
                                continue  # destino debe ir después del transbordo en B
                            dest_stop = obj_b[d_sid]

                            seg_a  = _build_stop_sequence(route_a, o_idx, rs_a.order_index)
                            seg_b  = _build_stop_sequence(route_b, t_idx_b, d_idx)
                            bus_km = route_distance_km(seg_a) + route_distance_km(seg_b)
                            w1     = _walk1(origin_stop)
                            w2     = _walk2(dest_stop)
                            total_t = _total_time_min(
                                w1, bus_km, w2, transfer_walk_km,
                                settings.BUS_AVG_SPEED_KMH
                            )
                            transfer_results.append(TransferRouteResult(
                                route_a=route_a,
                                route_b=route_b,
                                from_stop=origin_stop,
                                transfer_stop=ta_stop,
                                transfer_stop_b=tb_stop if tb_stop.id != ta_stop.id else None,
                                to_stop=dest_stop,
                                distance_km=round(bus_km, 2),
                                time_min=total_t,
                                walk1_km=round(w1, 3),
                                walk2_km=round(w2, 3),
                                transfer_walk_m=round(transfer_walk_km * 1000),
                            ))
                            if len(transfer_results) >= settings.MAX_TRANSFER_RESULTS * 10:
                                break
                        if len(transfer_results) >= settings.MAX_TRANSFER_RESULTS * 10:
                            break
                    if len(transfer_results) >= settings.MAX_TRANSFER_RESULTS * 10:
                        break
                if len(transfer_results) >= settings.MAX_TRANSFER_RESULTS * 10:
                    break
            if len(transfer_results) >= settings.MAX_TRANSFER_RESULTS * 10:
                break

    # 5. Ordenar por tiempo total (incluye caminatas) y truncar
    direct_results.sort(key=lambda r: r.time_min)
    transfer_results.sort(key=lambda r: r.time_min)

    # Deduplicar transfers: mismo route_a + route_b puede aparecer muchas veces
    seen_pairs: set[tuple] = set()
    deduped_transfers: List[TransferRouteResult] = []
    for t in transfer_results:
        key = (t.route_a.id, t.route_b.id)
        if key not in seen_pairs:
            seen_pairs.add(key)
            deduped_transfers.append(t)
        if len(deduped_transfers) >= settings.MAX_TRANSFER_RESULTS:
            break

    return SearchResponse(
        origin_query=origin,
        destination_query=destination,
        direct=direct_results[:settings.MAX_DIRECT_RESULTS],
        transfers=deduped_transfers,
        total_results=len(direct_results) + len(deduped_transfers),
    )


