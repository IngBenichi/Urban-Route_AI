from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import AdminUser
from app.models.route import Route
from app.models.route_stop import RouteStop
from app.schemas.route import RouteCreate, RouteUpdate, RouteOut, RouteWithStops
from app.schemas.stop import StopInRoute

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("", response_model=List[RouteOut])
async def list_routes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    fuente: Optional[str] = Query(None, description="Filtrar por fuente, ej. 'ambq_resolucion'"),
    empresa: Optional[str] = Query(None, description="Filtrar por empresa operadora"),
    db: AsyncSession = Depends(get_db),
):
    q = select(Route)
    if fuente:
        q = q.where(Route.fuente == fuente)
    if empresa:
        q = q.where(Route.empresa == empresa)
    result = await db.execute(q.offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/{route_id}", response_model=RouteWithStops)
async def get_route(route_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Route)
        .where(Route.id == route_id)
        .options(selectinload(Route.route_stops).selectinload(RouteStop.stop))
    )
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ruta no encontrada")

    stops = [
        StopInRoute(
            id=rs.stop.id,
            name=rs.stop.name,
            lat=rs.stop.lat,
            lon=rs.stop.lon,
            code=rs.stop.code,
            order_index=rs.order_index,
        )
        for rs in sorted(route.route_stops, key=lambda x: x.order_index)
    ]
    return RouteWithStops(**RouteOut.model_validate(route).model_dump(), stops=stops)


@router.post("", response_model=RouteOut, status_code=status.HTTP_201_CREATED)
async def create_route(
    body: RouteCreate,
    _: AdminUser,
    db: AsyncSession = Depends(get_db),
):
    route = Route(name=body.name, code=body.code, color=body.color)
    db.add(route)
    await db.flush()

    for stop_ref in (body.stops or []):
        rs = RouteStop(route_id=route.id, stop_id=stop_ref.stop_id, order_index=stop_ref.order_index)
        db.add(rs)

    await db.commit()
    await db.refresh(route)
    return route


@router.put("/{route_id}", response_model=RouteOut)
async def update_route(
    route_id: int,
    body: RouteUpdate,
    _: AdminUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Route).where(Route.id == route_id))
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ruta no encontrada")

    update_data = body.model_dump(exclude_unset=True, exclude={"stops"})
    for field, value in update_data.items():
        setattr(route, field, value)

    if body.stops is not None:
        # Reemplazar stops de la ruta
        await db.execute(
            RouteStop.__table__.delete().where(RouteStop.route_id == route_id)
        )
        for stop_ref in body.stops:
            rs = RouteStop(route_id=route_id, stop_id=stop_ref.stop_id, order_index=stop_ref.order_index)
            db.add(rs)

    await db.commit()
    await db.refresh(route)
    return route


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route(route_id: int, _: AdminUser, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Route).where(Route.id == route_id))
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ruta no encontrada")
    await db.delete(route)
    await db.commit()
