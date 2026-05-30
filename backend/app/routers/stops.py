from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import AdminUser
from app.models.stop import Stop
from app.schemas.stop import StopCreate, StopUpdate, StopOut

router = APIRouter(prefix="/stops", tags=["stops"])


@router.get("", response_model=List[StopOut])
async def list_stops(
    q: str = Query(None, description="Filtrar por nombre"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Stop).offset(skip).limit(limit)
    if q:
        stmt = stmt.where(Stop.name.ilike(f"%{q}%"))
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{stop_id}", response_model=StopOut)
async def get_stop(stop_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Stop).where(Stop.id == stop_id))
    stop = result.scalar_one_or_none()
    if not stop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paradero no encontrado")
    return stop


@router.post("", response_model=StopOut, status_code=status.HTTP_201_CREATED)
async def create_stop(body: StopCreate, _: AdminUser, db: AsyncSession = Depends(get_db)):
    stop = Stop(**body.model_dump())
    db.add(stop)
    await db.commit()
    await db.refresh(stop)
    return stop


@router.put("/{stop_id}", response_model=StopOut)
async def update_stop(
    stop_id: int,
    body: StopUpdate,
    _: AdminUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Stop).where(Stop.id == stop_id))
    stop = result.scalar_one_or_none()
    if not stop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paradero no encontrado")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(stop, field, value)
    await db.commit()
    await db.refresh(stop)
    return stop


@router.delete("/{stop_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stop(stop_id: int, _: AdminUser, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Stop).where(Stop.id == stop_id))
    stop = result.scalar_one_or_none()
    if not stop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paradero no encontrado")
    await db.delete(stop)
    await db.commit()
